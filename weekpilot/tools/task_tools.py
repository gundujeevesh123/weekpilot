"""
WeekPilot Task Tools — CRUD + Eisenhower prioritisation for tasks.

All functions receive ``tool_context`` as their first parameter (Google ADK
convention) and read/write ``tool_context.state["tasks"]``.
Return values are plain ``dict``s so ADK can serialise them for the LLM.
"""

from __future__ import annotations

from weekpilot.models.schemas import Task, ToolResponse
from weekpilot.tools.validators import (
    sanitize_text,
    validate_category,
    validate_date,
    validate_priority,
    ALLOWED_PRIORITIES,
    ALLOWED_CATEGORIES,
    ALLOWED_STATUSES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PRIORITY_ORDER = {
    "urgent-important": 0,
    "important": 1,
    "urgent": 2,
    "low": 3,
}


def _ensure_task_state(tool_context) -> list[dict]:
    """Initialise ``state['tasks']`` if it does not exist yet."""
    if "tasks" not in tool_context.state:
        tool_context.state["tasks"] = []
    return tool_context.state["tasks"]


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


def add_task(
    tool_context,
    title: str,
    priority: str = "low",
    category: str = "personal",
    deadline: str = "",
    description: str = "",
) -> dict:
    """Create a new task and add it to the task list.

    Use this tool whenever the user wants to create, add, or schedule a new
    task.  The task is classified using an Eisenhower-matrix priority.

    Args:
        tool_context: ADK tool context (auto-injected).
        title: Short title for the task (required).
        priority: One of 'urgent-important', 'important', 'urgent', 'low'.
        category: One of 'work', 'personal', 'health', 'errands', 'learning'.
        deadline: Optional deadline in YYYY-MM-DD format.
        description: Optional longer description of the task.

    Returns:
        dict with status, message, and the created task data.
    """
    tasks = _ensure_task_state(tool_context)

    # --- Validate title ---
    title = sanitize_text(title, max_length=200)
    if not title:
        return ToolResponse(
            status="error",
            message="Task title cannot be empty.",
        ).model_dump()

    # --- Validate priority ---
    priority = priority.lower().strip()
    if not validate_priority(priority):
        return ToolResponse(
            status="error",
            message=f"Invalid priority '{priority}'. Allowed: {sorted(ALLOWED_PRIORITIES)}",
        ).model_dump()

    # --- Validate category ---
    category = category.lower().strip()
    if not validate_category(category):
        return ToolResponse(
            status="error",
            message=f"Invalid category '{category}'. Allowed: {sorted(ALLOWED_CATEGORIES)}",
        ).model_dump()

    # --- Validate deadline (if provided) ---
    deadline_value = None
    if deadline:
        deadline = deadline.strip()
        if not validate_date(deadline):
            return ToolResponse(
                status="error",
                message=f"Invalid deadline '{deadline}'. Use YYYY-MM-DD format.",
            ).model_dump()
        deadline_value = deadline

    description = sanitize_text(description, max_length=1000)

    # --- Build & persist ---
    task = Task(
        title=title,
        description=description,
        priority=priority,
        category=category,
        deadline=deadline_value,
    )
    tasks.append(task.model_dump())
    tool_context.state["tasks"] = tasks  # write back to state

    return ToolResponse(
        status="success",
        message=f"Task '{title}' created (ID: {task.id}).",
        data=task.model_dump(),
    ).model_dump()


def list_tasks(
    tool_context,
    status_filter: str = "",
    priority_filter: str = "",
    category_filter: str = "",
) -> dict:
    """List tasks, optionally filtering by status, priority, or category.

    Use this tool when the user asks to see, list, or review their tasks.

    Args:
        tool_context: ADK tool context (auto-injected).
        status_filter: Filter by status ('todo', 'in_progress', 'done', 'cancelled'). Empty = all.
        priority_filter: Filter by priority. Empty = all.
        category_filter: Filter by category. Empty = all.

    Returns:
        dict with status, message, and filtered list of tasks.
    """
    tasks = _ensure_task_state(tool_context)

    filtered = list(tasks)  # shallow copy

    if status_filter:
        status_filter = status_filter.lower().strip()
        if status_filter not in ALLOWED_STATUSES:
            return ToolResponse(
                status="error",
                message=f"Invalid status filter '{status_filter}'. Allowed: {sorted(ALLOWED_STATUSES)}",
            ).model_dump()
        filtered = [t for t in filtered if t.get("status") == status_filter]

    if priority_filter:
        priority_filter = priority_filter.lower().strip()
        if not validate_priority(priority_filter):
            return ToolResponse(
                status="error",
                message=f"Invalid priority filter '{priority_filter}'. Allowed: {sorted(ALLOWED_PRIORITIES)}",
            ).model_dump()
        filtered = [t for t in filtered if t.get("priority") == priority_filter]

    if category_filter:
        category_filter = category_filter.lower().strip()
        if not validate_category(category_filter):
            return ToolResponse(
                status="error",
                message=f"Invalid category filter '{category_filter}'. Allowed: {sorted(ALLOWED_CATEGORIES)}",
            ).model_dump()
        filtered = [t for t in filtered if t.get("category") == category_filter]

    return ToolResponse(
        status="success",
        message=f"Found {len(filtered)} task(s).",
        data={"tasks": filtered, "total": len(filtered)},
    ).model_dump()


def update_task(
    tool_context,
    task_id: str,
    status: str = "",
    priority: str = "",
) -> dict:
    """Update a task's status and/or priority by its ID.

    Use this tool when the user wants to mark a task as done, change its
    priority, or update its progress status.

    Args:
        tool_context: ADK tool context (auto-injected).
        task_id: The unique task ID to update.
        status: New status ('todo', 'in_progress', 'done', 'cancelled'). Empty = no change.
        priority: New priority. Empty = no change.

    Returns:
        dict with status, message, and updated task data.
    """
    tasks = _ensure_task_state(tool_context)

    task_id = task_id.strip()
    if not task_id:
        return ToolResponse(status="error", message="Task ID is required.").model_dump()

    # Locate the task
    target = None
    for t in tasks:
        if t.get("id") == task_id:
            target = t
            break

    if target is None:
        return ToolResponse(
            status="error",
            message=f"No task found with ID '{task_id}'.",
        ).model_dump()

    # Validate & apply status update
    if status:
        status = status.lower().strip()
        if status not in ALLOWED_STATUSES:
            return ToolResponse(
                status="error",
                message=f"Invalid status '{status}'. Allowed: {sorted(ALLOWED_STATUSES)}",
            ).model_dump()
        target["status"] = status

    # Validate & apply priority update
    if priority:
        priority = priority.lower().strip()
        if not validate_priority(priority):
            return ToolResponse(
                status="error",
                message=f"Invalid priority '{priority}'. Allowed: {sorted(ALLOWED_PRIORITIES)}",
            ).model_dump()
        target["priority"] = priority

    tool_context.state["tasks"] = tasks  # write back

    return ToolResponse(
        status="success",
        message=f"Task '{task_id}' updated.",
        data=target,
    ).model_dump()


def delete_task(tool_context, task_id: str) -> dict:
    """Delete a task by its ID, with a confirmation step.

    This tool uses a two-step flow: the first call returns a
    ``confirmation_required`` response.  Only when the user confirms and
    ``state['delete_confirmed']`` is set to ``True`` will the task actually
    be removed.

    Args:
        tool_context: ADK tool context (auto-injected).
        task_id: The unique task ID to delete.

    Returns:
        dict asking for confirmation, or confirming deletion.
    """
    tasks = _ensure_task_state(tool_context)

    task_id = task_id.strip()
    if not task_id:
        return ToolResponse(status="error", message="Task ID is required.").model_dump()

    # Locate the task
    target = None
    target_idx = None
    for idx, t in enumerate(tasks):
        if t.get("id") == task_id:
            target = t
            target_idx = idx
            break

    if target is None:
        return ToolResponse(
            status="error",
            message=f"No task found with ID '{task_id}'.",
        ).model_dump()

    # Check for confirmation
    confirmed = tool_context.state.get("delete_confirmed", False)

    if not confirmed:
        # First call — ask for user confirmation
        return ToolResponse(
            status="confirmation_required",
            message=f"Are you sure you want to delete task '{target.get('title', task_id)}'? "
            "Please confirm to proceed.",
            data=target,
        ).model_dump()

    # Confirmed — remove the task
    tasks.pop(target_idx)
    tool_context.state["tasks"] = tasks
    # Reset the flag so future deletes require re-confirmation
    tool_context.state["delete_confirmed"] = False

    return ToolResponse(
        status="success",
        message=f"Task '{task_id}' has been deleted.",
        data=target,
    ).model_dump()


def prioritize_tasks(tool_context) -> dict:
    """Sort tasks by Eisenhower-matrix priority and return organised groups.

    Use this tool when the user asks to prioritise, rank, or triage their
    tasks.  Returns tasks grouped by priority quadrant.

    Args:
        tool_context: ADK tool context (auto-injected).

    Returns:
        dict with prioritised task groups and a flat sorted list.
    """
    tasks = _ensure_task_state(tool_context)

    # Only consider active tasks (not done/cancelled)
    active = [t for t in tasks if t.get("status") in ("todo", "in_progress")]

    if not active:
        return ToolResponse(
            status="success",
            message="No active tasks to prioritise.",
            data={"groups": {}, "sorted_tasks": []},
        ).model_dump()

    # Sort by priority order, then by deadline (None last)
    sorted_tasks = sorted(
        active,
        key=lambda t: (
            _PRIORITY_ORDER.get(t.get("priority", "low"), 99),
            t.get("deadline") or "9999-12-31",
        ),
    )

    # Group by priority
    groups: dict[str, list[dict]] = {}
    for t in sorted_tasks:
        pri = t.get("priority", "low")
        groups.setdefault(pri, []).append(t)

    return ToolResponse(
        status="success",
        message=f"Prioritised {len(sorted_tasks)} active task(s).",
        data={"groups": groups, "sorted_tasks": sorted_tasks},
    ).model_dump()
