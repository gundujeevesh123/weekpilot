"""
WeekPilot MCP Server — exposes public-data tools over MCP (stdio transport).

WHY AN MCP SERVER?
It demonstrates the Model Context Protocol course concept and cleanly separates
"world" tools (weather, time) from the agent. The WeekPilot schedule planner
connects to this server via ADK's ``McpToolset`` (see
``weekpilot/agents/schedule_planner.py``).

SECURITY / PRIVACY DESIGN (confidentiality, integrity, availability)
- **Transport = stdio.** The server is launched as a local child process and
  speaks only over stdin/stdout. No TCP port is opened, so nothing is reachable
  over the network — there is no remote attack surface.
- **No PII crosses this boundary.** Only public data is handled here: city names
  and timezones. Tasks, reminders, messages and any personal data stay in the
  agent's in-process session state and never reach this server.
- **No secrets.** The weather source (wttr.in) needs no API key, so this process
  holds no credentials.
- **Defensive I/O.** Inputs are sanitised and clamped; the external weather
  response is treated as untrusted and only an allow-list of fields is returned
  (see ``tools_impl``). The agent additionally re-scans every tool result for PII
  and secrets via its ``after_tool`` security callback.

Run standalone (for a quick check):  python -m weekpilot.mcp_server.server
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from weekpilot.mcp_server import tools_impl

# Server identity advertised to MCP clients during the handshake.
mcp = FastMCP("weekpilot-public-tools")


@mcp.tool()
def get_weather_forecast(city: str, days: int = 3) -> dict:
    """Get current weather and a 1-3 day forecast for a city (public data, no PII).

    Args:
        city: City name to look up, e.g. "London" or "New York".
        days: Number of forecast days (1-3, values outside are clamped).

    Returns:
        A dict with ``status``, ``message`` and ``data`` (current + forecast).
    """
    return tools_impl.weather_forecast(city, days)


@mcp.tool()
def get_current_datetime(timezone_name: str = "UTC") -> dict:
    """Get the current date/time and this week's Monday for an IANA timezone.

    Use this to anchor weekly planning to real dates. Non-PII (timezone only).

    Args:
        timezone_name: IANA timezone such as "UTC", "Europe/London", or
            "Asia/Kolkata". Defaults to "UTC".

    Returns:
        A dict with ``status``, ``message`` and ``data`` (date, time, weekday,
        and the date of the current week's Monday).
    """
    return tools_impl.current_datetime(timezone_name)


def main() -> None:
    """Start the MCP server over stdio (the default FastMCP transport)."""
    mcp.run()


if __name__ == "__main__":
    main()
