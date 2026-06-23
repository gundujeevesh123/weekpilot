"""
WeekPilot Tools Package — exposes all tool functions for easy registration.

Usage::

    from weekpilot.tools import add_task, set_reminder, draft_message, get_weather_forecast
"""

from __future__ import annotations

# -- Task tools ---------------------------------------------------------------
from weekpilot.tools.task_tools import (
    add_task,
    list_tasks,
    update_task,
    delete_task,
    prioritize_tasks,
)

# -- Reminder tools -----------------------------------------------------------
from weekpilot.tools.reminder_tools import (
    set_reminder,
    list_reminders,
    dismiss_reminder,
)

# -- Message tools ------------------------------------------------------------
from weekpilot.tools.message_tools import (
    draft_message,
    list_drafts,
    approve_draft,
)

# -- Weather tools ------------------------------------------------------------
from weekpilot.tools.weather_tools import (
    get_weather_forecast,
)

__all__ = [
    # Tasks
    "add_task",
    "list_tasks",
    "update_task",
    "delete_task",
    "prioritize_tasks",
    # Reminders
    "set_reminder",
    "list_reminders",
    "dismiss_reminder",
    # Messages
    "draft_message",
    "list_drafts",
    "approve_draft",
    # Weather
    "get_weather_forecast",
]
