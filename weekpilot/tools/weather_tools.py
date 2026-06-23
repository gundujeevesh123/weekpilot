"""
WeekPilot Weather Tools — fetch weather forecasts from wttr.in.

Uses the free ``wttr.in`` REST API (no API key needed).  Returns current
conditions and a multi-day forecast.

All functions receive ``tool_context`` as their first parameter (Google ADK
convention).  Return values are plain ``dict``s for ADK serialisation.
"""

from __future__ import annotations

import requests
import requests.exceptions

from weekpilot.models.schemas import ToolResponse
from weekpilot.tools.validators import sanitize_city_name


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_WTTR_URL = "https://wttr.in/{city}?format=j1"
_TIMEOUT_SECONDS = 5
_MAX_FORECAST_DAYS = 3
_MIN_FORECAST_DAYS = 1


# ---------------------------------------------------------------------------
# Tool function
# ---------------------------------------------------------------------------


def get_weather_forecast(tool_context, city: str, days: int = 3) -> dict:
    """Fetch the current weather and multi-day forecast for a city.

    Use this tool when the user asks about the weather, temperature, or
    forecast for a location.

    Args:
        tool_context: ADK tool context (auto-injected).
        city: City name to look up (e.g. 'London', 'New York').
        days: Number of forecast days (1-3). Values outside this range
              are clamped automatically.

    Returns:
        dict with status, message, and weather data (current + forecast).
    """
    # --- Sanitise city ---
    city = sanitize_city_name(city)
    if not city:
        return ToolResponse(
            status="error",
            message="City name cannot be empty. Please provide a valid city name.",
        ).model_dump()

    # --- Clamp days ---
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = _MAX_FORECAST_DAYS
    days = max(_MIN_FORECAST_DAYS, min(_MAX_FORECAST_DAYS, days))

    # --- Fetch data from wttr.in ---
    url = _WTTR_URL.format(city=city)

    try:
        response = requests.get(url, timeout=_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        return ToolResponse(
            status="error",
            message=f"Weather request for '{city}' timed out. Please try again later.",
        ).model_dump()
    except requests.exceptions.ConnectionError:
        return ToolResponse(
            status="error",
            message=f"Could not connect to the weather service. Please check your internet connection.",
        ).model_dump()
    except requests.exceptions.HTTPError as exc:
        return ToolResponse(
            status="error",
            message=f"Weather service returned an error for '{city}': {exc}",
        ).model_dump()
    except requests.exceptions.RequestException as exc:
        return ToolResponse(
            status="error",
            message=f"Failed to fetch weather for '{city}': {exc}",
        ).model_dump()
    except (ValueError, KeyError):
        return ToolResponse(
            status="error",
            message=f"Received invalid data from the weather service for '{city}'.",
        ).model_dump()

    # --- Parse current conditions ---
    try:
        current_raw = data["current_condition"][0]
        current = {
            "temp_c": current_raw.get("temp_C", "N/A"),
            "temp_f": current_raw.get("temp_F", "N/A"),
            "condition": (
                current_raw.get("weatherDesc", [{}])[0].get("value", "Unknown")
            ),
            "humidity": current_raw.get("humidity", "N/A"),
            "feels_like_c": current_raw.get("FeelsLikeC", "N/A"),
            "wind_speed_kmph": current_raw.get("windspeedKmph", "N/A"),
        }
    except (KeyError, IndexError, TypeError):
        current = {"error": "Could not parse current conditions."}

    # --- Parse daily forecasts ---
    forecasts: list[dict] = []
    try:
        weather_list = data.get("weather", [])
        for day_data in weather_list[:days]:
            hourly = day_data.get("hourly", [])
            # Pick midday description if available
            description = "N/A"
            if len(hourly) > 4:
                desc_list = hourly[4].get("weatherDesc", [{}])
                description = desc_list[0].get("value", "N/A") if desc_list else "N/A"
            elif hourly:
                desc_list = hourly[0].get("weatherDesc", [{}])
                description = desc_list[0].get("value", "N/A") if desc_list else "N/A"

            forecasts.append(
                {
                    "date": day_data.get("date", "N/A"),
                    "max_temp_c": day_data.get("maxtempC", "N/A"),
                    "min_temp_c": day_data.get("mintempC", "N/A"),
                    "max_temp_f": day_data.get("maxtempF", "N/A"),
                    "min_temp_f": day_data.get("mintempF", "N/A"),
                    "description": description,
                    "avg_humidity": day_data.get("avgtempC", "N/A"),  # fallback
                }
            )
    except (KeyError, TypeError):
        forecasts = [{"error": "Could not parse forecast data."}]

    return ToolResponse(
        status="success",
        message=f"Weather forecast for {city} ({days} day(s)).",
        data={
            "city": city,
            "current": current,
            "forecast": forecasts,
        },
    ).model_dump()
