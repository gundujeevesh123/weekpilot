"""
Tests for the WeekPilot MCP server's tool logic (``weekpilot.mcp_server.tools_impl``).

These exercise the transport-independent logic directly, so they run offline and
without spawning an MCP server or making network calls. They also act as a
security regression guard: inputs must be sanitised and bad input must fail
closed (an ``error`` status, never an exception or a network call).
"""

from __future__ import annotations

from datetime import date

from weekpilot.mcp_server import tools_impl


class TestInputSanitisation:
    def test_sanitize_city_strips_unsafe_characters(self):
        # Symbols, slashes and brackets are removed; letters, spaces and hyphens kept.
        assert tools_impl.sanitize_city("Lon<>don") == "London"
        assert tools_impl.sanitize_city("New York!@#") == "New York"
        assert tools_impl.sanitize_city("Stratford-upon-Avon") == "Stratford-upon-Avon"

    def test_sanitize_city_length_capped(self):
        assert len(tools_impl.sanitize_city("a" * 500)) == 100

    def test_sanitize_timezone_defaults_to_utc(self):
        assert tools_impl.sanitize_timezone("") == "UTC"
        # Disallowed characters stripped, valid IANA chars kept.
        assert tools_impl.sanitize_timezone("Europe/London;rm -rf") == "Europe/Londonrm-rf"


class TestCurrentDatetime:
    def test_utc_success_shape(self):
        result = tools_impl.current_datetime("UTC")
        assert result["status"] == "success"
        data = result["data"]
        for key in ("timezone", "iso_datetime", "date", "time", "weekday", "week_of_monday"):
            assert key in data
        # week_of_monday must actually be a Monday (weekday() == 0).
        assert date.fromisoformat(data["week_of_monday"]).weekday() == 0

    def test_named_timezone_supported(self):
        result = tools_impl.current_datetime("Asia/Kolkata")
        assert result["status"] == "success"
        assert result["data"]["timezone"] == "Asia/Kolkata"

    def test_unknown_timezone_fails_closed(self):
        result = tools_impl.current_datetime("Not/AReal_Zone")
        assert result["status"] == "error"


class TestWeatherForecast:
    def test_empty_city_errors_without_network(self):
        # A blank/garbage city must short-circuit to an error BEFORE any network
        # call (the sanitiser reduces it to an empty string).
        assert tools_impl.weather_forecast("")["status"] == "error"
        assert tools_impl.weather_forecast("<>{}")["status"] == "error"
