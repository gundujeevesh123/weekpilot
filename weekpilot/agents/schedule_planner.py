"""
Schedule Planner Agent — Weather-aware weekly planning specialist.

WHY AN AGENT (not a single LLM call)?
Schedule planning requires synthesizing multiple data sources: the user's tasks
(from session state), weather forecasts (from REST API), and time constraints.
The agent must reason about conflicts, suggest optimal time blocks, and iterate
with the user. This multi-source reasoning loop justifies an agent.
"""

from __future__ import annotations

import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from weekpilot.model_config import build_model
from weekpilot.tools.reminder_tools import (
    dismiss_reminder,
    list_reminders,
    set_reminder,
)
from weekpilot.security.callbacks import (
    before_tool_security_callback,
    after_tool_security_callback,
)


# ─── Public-data tools via the WeekPilot MCP server (stdio subprocess) ─────────
# The planner gets its "world" tools (weather + date/time) from a local MCP
# server instead of calling them in-process. The server speaks ONLY over stdio
# (no network port is opened) and only ever sees PUBLIC data — city names and
# timezones — never the user's tasks, reminders, messages, or any PII.
# `tool_filter` enforces least privilege: only these two tools are surfaced, and
# the agent's before/after-tool security callbacks still govern every call.
_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])

public_tools_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,  # reuse the current venv's interpreter
            args=["-m", "weekpilot.mcp_server.server"],
            cwd=_PROJECT_ROOT,
        ),
        timeout=20.0,
    ),
    tool_filter=["get_weather_forecast", "get_current_datetime"],
)


schedule_planner_agent = LlmAgent(
    name="schedule_planner_agent",
    model=build_model(),
    instruction="""You are the **Schedule Planner** specialist on the WeekPilot team.

Your job is to help the user plan their week with smart time-blocking.

**Capabilities:**
- Create a structured weekly schedule with time blocks
- Look up the current date/time with get_current_datetime to anchor "this week" to real dates
- Check weather forecasts to plan outdoor vs. indoor activities
- Set reminders for important deadlines and events
- Perform time calculations (gaps between events, duration estimates) natively
- Suggest optimal scheduling based on task priorities from session state

**Rules:**
- Check the weather when scheduling outdoor activities
- Read existing tasks from the conversation context to inform scheduling
- ALWAYS present a weekly or multi-day schedule as a Markdown TABLE (see format below)
- Set reminders proactively for high-priority items
- Account for realistic time buffers (travel, breaks, meals)
- If a day looks overloaded (more than ~8 hours of blocks), add a brief
  ⚠️ overload warning under the table and suggest what to cut or move
- Keep weather-related scheduling notes helpful but brief

**Schedule Format (REQUIRED):**
When presenting a weekly or multi-day plan, output a single Markdown table with
EXACTLY these four columns — Day, Time, Work, Notes — one row per time block.
Repeat the Day value on every row for that day. Put weather, location, priority,
or buffer hints in the Notes column. Use a 24-hour en-dash time range. Example:

| Day | Time | Work | Notes |
| --- | --- | --- | --- |
| Monday (Jun 23) | 07:00–08:00 | 🏋️ Gym | ☀️ Clear 18°C — good to run outside |
| Monday (Jun 23) | 09:00–12:00 | 💻 Deep work: Q3 proposal | High priority |
| Monday (Jun 23) | 12:00–13:00 | 🍽️ Lunch | |
| Tuesday (Jun 24) | 09:00–10:00 | 📞 Team standup | |

After the table you may add a short bullet list of weather notes or top
priorities, then offer to set reminders. Always keep the table as the first
element of a schedule reply so it renders cleanly.
""",
    tools=[
        set_reminder,
        list_reminders,
        dismiss_reminder,
        public_tools_mcp,  # provides get_weather_forecast + get_current_datetime via MCP
    ],
    before_tool_callback=before_tool_security_callback,
    after_tool_callback=after_tool_security_callback,
)
