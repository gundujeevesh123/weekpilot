"""
WeekPilot Reminder Tools — create, list, and dismiss time-based reminders.

All functions receive ``tool_context`` as their first parameter (Google ADK
convention) and read/write ``tool_context.state["reminders"]``.
Return values are plain ``dict``s so ADK can serialise them for the LLM.
"""

from __future__ import annotations

from weekpilot.models.schemas import Reminder, ToolResponse
from weekpilot.tools.validators import (
    sanitize_text,
    validate_datetime,
    ALLOWED_REMINDER_STATUSES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_reminder_state(tool_context) -> list[dict]:
    """Initialise ``state['reminders']`` if it does not exist yet."""
    if "reminders" not in tool_context.state:
        tool_context.state["reminders"] = []
    return tool_context.state["reminders"]


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


def set_reminder(
    tool_context,
    message: str,
    due_time: str,
    recurring: bool = False,
) -> dict:
    """Create a new time-based reminder.

    Use this tool when the user wants to be reminded of something at a
    specific date and time.

    Args:
        tool_context: ADK tool context (auto-injected).
        message: The reminder text (what to remind the user about).
        due_time: When the reminder should fire, in YYYY-MM-DDTHH:MM format.
        recurring: If True the reminder repeats weekly.

    Returns:
        dict with status, message, and the created reminder data.
    """
    reminders = _ensure_reminder_state(tool_context)

    # --- Validate message ---
    message = sanitize_text(message, max_length=500)
    if not message:
        return ToolResponse(
            status="error",
            message="Reminder message cannot be empty.",
        ).model_dump()

    # --- Validate due_time ---
    due_time = due_time.strip()
    if not validate_datetime(due_time):
        return ToolResponse(
            status="error",
            message=f"Invalid due_time '{due_time}'. Use YYYY-MM-DDTHH:MM format.",
        ).model_dump()

    # --- Validate recurring ---
    if not isinstance(recurring, bool):
        recurring = bool(recurring)

    # --- Build & persist ---
    reminder = Reminder(
        message=message,
        due_time=due_time,
        recurring=recurring,
    )
    reminders.append(reminder.model_dump())
    tool_context.state["reminders"] = reminders  # write back

    return ToolResponse(
        status="success",
        message=f"Reminder set for {due_time} (ID: {reminder.id}).",
        data=reminder.model_dump(),
    ).model_dump()


def list_reminders(tool_context, status_filter: str = "") -> dict:
    """List reminders, optionally filtering by status.

    Use this tool when the user asks to see or review their reminders.

    Args:
        tool_context: ADK tool context (auto-injected).
        status_filter: Filter by status ('pending', 'triggered', 'dismissed'). Empty = all.

    Returns:
        dict with status, message, and list of reminders.
    """
    reminders = _ensure_reminder_state(tool_context)

    filtered = list(reminders)

    if status_filter:
        status_filter = status_filter.lower().strip()
        if status_filter not in ALLOWED_REMINDER_STATUSES:
            return ToolResponse(
                status="error",
                message=(
                    f"Invalid status filter '{status_filter}'. "
                    f"Allowed: {sorted(ALLOWED_REMINDER_STATUSES)}"
                ),
            ).model_dump()
        filtered = [r for r in filtered if r.get("status") == status_filter]

    return ToolResponse(
        status="success",
        message=f"Found {len(filtered)} reminder(s).",
        data={"reminders": filtered, "total": len(filtered)},
    ).model_dump()


def dismiss_reminder(tool_context, reminder_id: str) -> dict:
    """Dismiss a reminder by its ID.

    Use this tool when the user wants to dismiss or silence a reminder.

    Args:
        tool_context: ADK tool context (auto-injected).
        reminder_id: The unique reminder ID to dismiss.

    Returns:
        dict with status, message, and updated reminder data.
    """
    reminders = _ensure_reminder_state(tool_context)

    reminder_id = reminder_id.strip()
    if not reminder_id:
        return ToolResponse(
            status="error",
            message="Reminder ID is required.",
        ).model_dump()

    # Locate the reminder
    target = None
    for r in reminders:
        if r.get("id") == reminder_id:
            target = r
            break

    if target is None:
        return ToolResponse(
            status="error",
            message=f"No reminder found with ID '{reminder_id}'.",
        ).model_dump()

    if target.get("status") == "dismissed":
        return ToolResponse(
            status="success",
            message=f"Reminder '{reminder_id}' is already dismissed.",
            data=target,
        ).model_dump()

    target["status"] = "dismissed"
    tool_context.state["reminders"] = reminders  # write back

    return ToolResponse(
        status="success",
        message=f"Reminder '{reminder_id}' dismissed.",
        data=target,
    ).model_dump()
