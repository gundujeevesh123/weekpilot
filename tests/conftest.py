"""
WeekPilot test fixtures and shared test utilities.
"""

from __future__ import annotations

import pytest


class MockToolContext:
    """Simulates ADK's tool_context for unit testing tools.

    Provides a dict-like `state` attribute that mirrors how ADK
    passes session state to tool functions.
    """

    def __init__(self, initial_state: dict | None = None):
        self.state = initial_state or {}

    def __repr__(self) -> str:
        return f"MockToolContext(state_keys={list(self.state.keys())})"


@pytest.fixture
def tool_context():
    """Provide a fresh MockToolContext for each test."""
    return MockToolContext()


@pytest.fixture
def tool_context_with_tasks():
    """Provide a MockToolContext pre-loaded with sample tasks."""
    return MockToolContext(
        initial_state={
            "tasks": [
                {
                    "id": "task-001",
                    "title": "Prepare presentation",
                    "description": "Q3 review slides",
                    "priority": "urgent-important",
                    "category": "work",
                    "deadline": "2026-06-25",
                    "status": "todo",
                    "created_at": "2026-06-23T10:00:00",
                },
                {
                    "id": "task-002",
                    "title": "Buy groceries",
                    "description": "Milk, eggs, bread",
                    "priority": "low",
                    "category": "errands",
                    "deadline": "",
                    "status": "todo",
                    "created_at": "2026-06-23T10:05:00",
                },
                {
                    "id": "task-003",
                    "title": "Morning jog",
                    "description": "",
                    "priority": "important",
                    "category": "health",
                    "deadline": "",
                    "status": "done",
                    "created_at": "2026-06-23T08:00:00",
                },
            ]
        }
    )


@pytest.fixture
def tool_context_with_reminders():
    """Provide a MockToolContext pre-loaded with sample reminders."""
    return MockToolContext(
        initial_state={
            "reminders": [
                {
                    "id": "rem-001",
                    "message": "Team standup in 15 minutes",
                    "due_time": "2026-06-23T09:45",
                    "recurring": True,
                    "status": "pending",
                    "created_at": "2026-06-23T08:00:00",
                },
            ]
        }
    )


@pytest.fixture
def tool_context_with_drafts():
    """Provide a MockToolContext pre-loaded with sample message drafts."""
    return MockToolContext(
        initial_state={
            "drafts": [
                {
                    "id": "msg-001",
                    "recipient": "Team",
                    "subject": "Weekly Update",
                    "body": "Hi team, here's this week's update...",
                    "tone": "professional",
                    "channel": "email",
                    "status": "draft",
                    "created_at": "2026-06-23T10:00:00",
                },
            ]
        }
    )
