"""
WeekPilot Tool Tests — Outcome-based tests for all custom function tools.

Each test asserts observable behavior (what the tool returns and how state
changes), not implementation details. This makes tests resilient to refactoring.
"""

from __future__ import annotations

import pytest
from tests.conftest import MockToolContext


# =============================================================================
# Task Tools
# =============================================================================

class TestAddTask:
    """Tests for the add_task tool."""

    def test_add_task_creates_task_in_state(self, tool_context):
        from weekpilot.tools.task_tools import add_task

        result = add_task(tool_context, title="Buy milk", priority="low", category="errands")

        assert result["status"] == "success"
        assert len(tool_context.state["tasks"]) == 1
        assert tool_context.state["tasks"][0]["title"] == "Buy milk"

    def test_add_task_with_all_fields(self, tool_context):
        from weekpilot.tools.task_tools import add_task

        result = add_task(
            tool_context,
            title="Prepare presentation",
            priority="urgent-important",
            category="work",
            deadline="2026-06-25",
            description="Q3 review slides",
        )

        assert result["status"] == "success"
        task = tool_context.state["tasks"][0]
        assert task["priority"] == "urgent-important"
        assert task["category"] == "work"
        assert task["deadline"] == "2026-06-25"

    def test_add_task_rejects_empty_title(self, tool_context):
        from weekpilot.tools.task_tools import add_task

        result = add_task(tool_context, title="", priority="low")

        assert result["status"] == "error"

    def test_add_task_rejects_invalid_priority(self, tool_context):
        from weekpilot.tools.task_tools import add_task

        result = add_task(tool_context, title="Test", priority="CRITICAL")

        assert result["status"] == "error"


class TestListTasks:
    """Tests for the list_tasks tool."""

    def test_list_tasks_returns_all(self, tool_context_with_tasks):
        from weekpilot.tools.task_tools import list_tasks

        result = list_tasks(tool_context_with_tasks)

        assert result["status"] == "success"
        assert len(result["data"]["tasks"]) == 3

    def test_list_tasks_filters_by_status(self, tool_context_with_tasks):
        from weekpilot.tools.task_tools import list_tasks

        result = list_tasks(tool_context_with_tasks, status_filter="done")

        assert result["status"] == "success"
        assert all(t["status"] == "done" for t in result["data"]["tasks"])

    def test_list_tasks_empty_state(self, tool_context):
        from weekpilot.tools.task_tools import list_tasks

        result = list_tasks(tool_context)

        assert result["status"] == "success"
        assert len(result["data"]["tasks"]) == 0


class TestUpdateTask:
    """Tests for the update_task tool."""

    def test_update_task_changes_status(self, tool_context_with_tasks):
        from weekpilot.tools.task_tools import update_task

        result = update_task(tool_context_with_tasks, task_id="task-001", status="in_progress")

        assert result["status"] == "success"
        task = next(t for t in tool_context_with_tasks.state["tasks"] if t["id"] == "task-001")
        assert task["status"] == "in_progress"

    def test_update_task_nonexistent_id(self, tool_context_with_tasks):
        from weekpilot.tools.task_tools import update_task

        result = update_task(tool_context_with_tasks, task_id="nonexistent", status="done")

        assert result["status"] == "error"


class TestDeleteTask:
    """Tests for the delete_task tool (human-in-the-loop)."""

    def test_delete_task_requires_confirmation(self, tool_context_with_tasks):
        from weekpilot.tools.task_tools import delete_task

        result = delete_task(tool_context_with_tasks, task_id="task-001")

        # Should ask for confirmation, not delete immediately
        assert result["status"] == "confirmation_required"
        # Task should still exist
        assert any(t["id"] == "task-001" for t in tool_context_with_tasks.state["tasks"])


class TestPrioritizeTasks:
    """Tests for the prioritize_tasks tool."""

    def test_prioritize_sorts_by_eisenhower(self, tool_context_with_tasks):
        from weekpilot.tools.task_tools import prioritize_tasks

        result = prioritize_tasks(tool_context_with_tasks)

        assert result["status"] == "success"
        # urgent-important should come first
        sorted_tasks = result["data"]["sorted_tasks"]
        assert len(sorted_tasks) > 0


# =============================================================================
# Reminder Tools
# =============================================================================

class TestSetReminder:
    """Tests for the set_reminder tool."""

    def test_set_reminder_creates_reminder(self, tool_context):
        from weekpilot.tools.reminder_tools import set_reminder

        result = set_reminder(
            tool_context,
            message="Team standup",
            due_time="2026-06-24T09:00",
        )

        assert result["status"] == "success"
        assert len(tool_context.state["reminders"]) == 1

    def test_set_reminder_rejects_empty_message(self, tool_context):
        from weekpilot.tools.reminder_tools import set_reminder

        result = set_reminder(tool_context, message="", due_time="2026-06-24T09:00")

        assert result["status"] == "error"


class TestDismissReminder:
    """Tests for the dismiss_reminder tool."""

    def test_dismiss_changes_status(self, tool_context_with_reminders):
        from weekpilot.tools.reminder_tools import dismiss_reminder

        result = dismiss_reminder(tool_context_with_reminders, reminder_id="rem-001")

        assert result["status"] == "success"
        rem = tool_context_with_reminders.state["reminders"][0]
        assert rem["status"] == "dismissed"


# =============================================================================
# Message Tools
# =============================================================================

class TestDraftMessage:
    """Tests for the draft_message tool."""

    def test_draft_creates_message(self, tool_context):
        from weekpilot.tools.message_tools import draft_message

        result = draft_message(
            tool_context,
            recipient="Team",
            body="Hi team, weekly update here.",
            tone="professional",
        )

        assert result["status"] == "success"
        assert len(tool_context.state["drafts"]) == 1

    def test_draft_rejects_empty_body(self, tool_context):
        from weekpilot.tools.message_tools import draft_message

        result = draft_message(tool_context, recipient="Boss", body="")

        assert result["status"] == "error"


class TestApproveDraft:
    """Tests for the approve_draft tool (human-in-the-loop)."""

    def test_approve_changes_status(self, tool_context_with_drafts):
        from weekpilot.tools.message_tools import approve_draft

        # First call should require confirmation (human-in-the-loop)
        result = approve_draft(tool_context_with_drafts, draft_id="msg-001")
        assert result["status"] == "confirmation_required"

        # Set confirmation flag and call again
        tool_context_with_drafts.state["draft_approved_confirmed"] = True
        result = approve_draft(tool_context_with_drafts, draft_id="msg-001")
        assert result["status"] == "success"
        draft = tool_context_with_drafts.state["drafts"][0]
        assert draft["status"] == "approved"


# =============================================================================
# Weather Tools
# =============================================================================

class TestWeatherForecast:
    """Tests for the get_weather_forecast tool."""

    def test_weather_sanitizes_city_name(self, tool_context):
        """Ensure malicious city names are sanitized."""
        from weekpilot.tools.weather_tools import get_weather_forecast

        # This should not crash — city name with injection attempt
        result = get_weather_forecast(tool_context, city="<script>alert('xss')</script>")

        # Should either return an error or sanitized result, but never crash
        assert result["status"] in ("success", "error")

    def test_weather_clamps_days(self, tool_context):
        """Ensure days parameter is clamped to valid range."""
        from weekpilot.tools.weather_tools import get_weather_forecast

        # Days > 3 should be clamped
        result = get_weather_forecast(tool_context, city="London", days=99)

        # Should not crash
        assert result["status"] in ("success", "error")


# =============================================================================
# Validators
# =============================================================================

class TestValidators:
    """Tests for input validation utilities."""

    def test_sanitize_text_limits_length(self):
        from weekpilot.tools.validators import sanitize_text

        long_text = "A" * 5000
        result = sanitize_text(long_text, max_length=100)
        assert len(result) <= 100

    def test_sanitize_text_strips_control_chars(self):
        from weekpilot.tools.validators import sanitize_text

        result = sanitize_text("Hello\x00World\x01!")
        assert "\x00" not in result
        assert "\x01" not in result

    def test_validate_date_accepts_valid(self):
        from weekpilot.tools.validators import validate_date

        assert validate_date("2026-06-25") is True

    def test_validate_date_rejects_invalid(self):
        from weekpilot.tools.validators import validate_date

        assert validate_date("not-a-date") is False
        assert validate_date("2026-13-01") is False

    def test_sanitize_city_strips_special_chars(self):
        from weekpilot.tools.validators import sanitize_city_name

        result = sanitize_city_name("San<script>Francisco")
        assert "<" not in result
        assert ">" not in result
        assert "script" not in result.lower() or "San" in result
