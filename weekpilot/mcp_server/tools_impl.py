"""
WeekPilot MCP Tools — implementation (transport-independent).

This module holds the *logic* for the public-data tools exposed by the WeekPilot
MCP server. It deliberately has **no dependency on MCP or on the rest of the
WeekPilot package**, which keeps the security boundary clean and makes the logic
unit-testable without spawning a server.

SECURITY / PRIVACY NOTES
- Only PUBLIC, NON-PII data is handled here: city names and timezones. No tasks,
  reminders, messages, or any personal data ever reach this code.
- No secrets: the weather source (wttr.in) requires no API key.
- All inputs are sanitised; the external weather response is treated as
  untrusted and only an allow-list of fields is extracted.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

try:  # Python 3.9+ stdlib; on Windows the `tzdata` package supplies the DB.
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - very old runtimes only
    ZoneInfo = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_CITY_RE = re.compile(r"[^a-zA-Z0-9\s.\-]")
_TZ_RE = re.compile(r"[^A-Za-z0-9_/+\-]")
_WTTR_URL = "https://wttr.in/{city}?format=j1"
_TIMEOUT_SECONDS = 5
_MIN_FORECAST_DAYS = 1
_MAX_FORECAST_DAYS = 3


# ---------------------------------------------------------------------------
# Input sanitisation
# ---------------------------------------------------------------------------
def sanitize_city(city: str) -> str:
    """Keep only letters, digits, spaces, hyphens and periods; cap at 100 chars."""
    return _CITY_RE.sub("", str(city)).strip()[:100]


def sanitize_timezone(timezone_name: str) -> str:
    """Keep only characters valid in IANA timezone names (e.g. ``Europe/London``)."""
    return _TZ_RE.sub("", str(timezone_name)).strip()[:64] or "UTC"


# ---------------------------------------------------------------------------
# Tool logic
# ---------------------------------------------------------------------------
def weather_forecast(city: str, days: int = 3) -> dict:
    """Fetch current weather + a 1-3 day forecast for *city* from wttr.in.

    Args:
        city: City name (e.g. ``"London"``). Sanitised before use.
        days: Number of forecast days (1-3, clamped).

    Returns:
        A ``{"status", "message", "data"}`` dict. ``status`` is ``"success"`` or
        ``"error"``. Only whitelisted weather fields are returned.
    """
    city = sanitize_city(city)
    if not city:
        return {"status": "error", "message": "City name cannot be empty."}

    try:
        days = int(days)
    except (TypeError, ValueError):
        days = _MAX_FORECAST_DAYS
    days = max(_MIN_FORECAST_DAYS, min(_MAX_FORECAST_DAYS, days))

    # Lazy import so this module imports with stdlib only (test-friendly).
    import requests
    import requests.exceptions

    try:
        response = requests.get(
            _WTTR_URL.format(city=city), timeout=_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        return {"status": "error", "message": f"Weather request for '{city}' timed out."}
    except requests.exceptions.RequestException as exc:
        return {"status": "error", "message": f"Could not fetch weather for '{city}': {exc}"}
    except ValueError:
        return {"status": "error", "message": f"Invalid data from weather service for '{city}'."}

    # --- Parse current conditions (whitelist fields only) ---
    try:
        cur = data["current_condition"][0]
        current = {
            "temp_c": cur.get("temp_C", "N/A"),
            "temp_f": cur.get("temp_F", "N/A"),
            "condition": cur.get("weatherDesc", [{}])[0].get("value", "Unknown"),
            "humidity": cur.get("humidity", "N/A"),
            "feels_like_c": cur.get("FeelsLikeC", "N/A"),
            "wind_speed_kmph": cur.get("windspeedKmph", "N/A"),
        }
    except (KeyError, IndexError, TypeError):
        current = {"error": "Could not parse current conditions."}

    # --- Parse daily forecast (whitelist fields only) ---
    forecasts: list[dict] = []
    try:
        for day in data.get("weather", [])[:days]:
            hourly = day.get("hourly", [])
            slot = hourly[4] if len(hourly) > 4 else (hourly[0] if hourly else {})
            desc = (slot.get("weatherDesc", [{}]) or [{}])[0].get("value", "N/A")
            forecasts.append(
                {
                    "date": day.get("date", "N/A"),
                    "max_temp_c": day.get("maxtempC", "N/A"),
                    "min_temp_c": day.get("mintempC", "N/A"),
                    "description": desc,
                }
            )
    except (KeyError, TypeError, IndexError):
        forecasts = [{"error": "Could not parse forecast data."}]

    return {
        "status": "success",
        "message": f"Weather forecast for {city} ({days} day(s)).",
        "data": {"city": city, "current": current, "forecast": forecasts},
    }


def current_datetime(timezone_name: str = "UTC") -> dict:
    """Return the current date/time and the current week's Monday for a timezone.

    Gives the schedule planner a reliable clock so it can anchor "this week" to
    real dates instead of guessing. Non-PII (a timezone name only).

    Args:
        timezone_name: IANA timezone (e.g. ``"UTC"``, ``"Europe/London"``,
            ``"Asia/Kolkata"``). Defaults to UTC.

    Returns:
        A ``{"status", "message", "data"}`` dict.
    """
    tz_name = sanitize_timezone(timezone_name)

    if ZoneInfo is None:
        return {"status": "error", "message": "Timezone support is unavailable in this runtime."}

    try:
        tz = ZoneInfo(tz_name)
    except Exception:  # ZoneInfoNotFoundError or bad name
        return {
            "status": "error",
            "message": (
                f"Unknown timezone '{tz_name}'. Use an IANA name like 'UTC', "
                "'Europe/London', or 'Asia/Kolkata'."
            ),
        }

    now = datetime.now(tz)
    monday = (now - timedelta(days=now.weekday())).date()
    return {
        "status": "success",
        "message": f"Current date/time in {tz_name}.",
        "data": {
            "timezone": tz_name,
            "iso_datetime": now.isoformat(timespec="seconds"),
            "date": now.date().isoformat(),
            "time": now.strftime("%H:%M"),
            "weekday": now.strftime("%A"),
            "week_of_monday": monday.isoformat(),
        },
    }
