"""
WeekPilot Data Schemas — Pydantic models for all data contracts.

Every piece of structured data flowing through the system has a typed contract
defined here. This is the single source of truth for data shapes.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Task Management
# =============================================================================

class Task(BaseModel):
    """A user task with Eisenhower-matrix priority classification."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: str = Field(default="", max_length=1000, description="Optional details")
    priority: Literal["urgent-important", "important", "urgent", "low"] = Field(
        default="low",
        description="Eisenhower matrix quadrant",
    )
    category: Literal["work", "personal", "health", "errands", "learning"] = Field(
        default="personal",
        description="Task category",
    )
    deadline: Optional[str] = Field(
        default=None,
        description="ISO date string (YYYY-MM-DD), or None if no deadline",
    )
    status: Literal["todo", "in_progress", "done", "cancelled"] = Field(default="todo")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds"),
        description="ISO datetime when the task was created",
    )


# =============================================================================
# Reminders
# =============================================================================

class Reminder(BaseModel):
    """A time-based reminder for the user."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    message: str = Field(..., min_length=1, max_length=500, description="Reminder text")
    due_time: str = Field(
        ...,
        description="ISO datetime string (YYYY-MM-DDTHH:MM) when the reminder fires",
    )
    recurring: bool = Field(default=False, description="Whether this repeats weekly")
    status: Literal["pending", "triggered", "dismissed"] = Field(default="pending")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds"),
    )


# =============================================================================
# Message Drafts
# =============================================================================

class DraftMessage(BaseModel):
    """A drafted message awaiting user approval before 'sending'."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    recipient: str = Field(
        ..., min_length=1, max_length=200, description="Who the message is for"
    )
    subject: Optional[str] = Field(
        default=None, max_length=200, description="Subject line (for emails)"
    )
    body: str = Field(..., min_length=1, max_length=5000, description="Message body")
    tone: Literal["professional", "friendly", "formal", "casual"] = Field(
        default="professional",
        description="Writing tone",
    )
    channel: Literal["email", "chat", "sms"] = Field(
        default="email",
        description="Delivery channel",
    )
    status: Literal["draft", "approved", "sent"] = Field(default="draft")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds"),
    )


# =============================================================================
# Week Planning
# =============================================================================

class WeekPlan(BaseModel):
    """A structured weekly plan with time-blocked activities."""

    week_of: str = Field(..., description="ISO date of Monday (YYYY-MM-DD)")
    days: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "Monday": [], "Tuesday": [], "Wednesday": [],
            "Thursday": [], "Friday": [], "Saturday": [], "Sunday": [],
        },
        description="Day name → list of time-blocked activities",
    )
    priorities: list[str] = Field(
        default_factory=list,
        description="Top priorities for the week",
    )
    weather_notes: Optional[str] = Field(
        default=None,
        description="Weather-related scheduling notes",
    )


# =============================================================================
# Security / Privacy
# =============================================================================

class SensitiveDataFlag(BaseModel):
    """Flags a piece of data as potentially sensitive, requiring consent."""

    field_name: str = Field(..., description="Which field contains sensitive data")
    data_type: Literal["email", "phone", "address", "financial", "health", "name"] = Field(
        ..., description="Category of sensitive data detected"
    )
    value_preview: str = Field(
        default="[REDACTED]",
        description="Redacted preview of the detected value",
    )
    requires_consent: bool = Field(
        default=True,
        description="Whether user consent is needed before persisting",
    )


class ConsentRequest(BaseModel):
    """A request for user consent to persist sensitive data."""

    data_description: str = Field(
        ..., description="Human-readable description of what will be stored"
    )
    sensitive_fields: list[SensitiveDataFlag] = Field(
        default_factory=list,
        description="List of sensitive fields detected",
    )
    approved: Optional[bool] = Field(
        default=None,
        description="None=pending, True=approved, False=denied",
    )


# =============================================================================
# Tool Response Envelope
# =============================================================================

class ToolResponse(BaseModel):
    """Standard envelope for all tool responses — ensures consistent structure."""

    status: Literal["success", "error", "confirmation_required"] = Field(
        ..., description="Outcome status"
    )
    message: str = Field(..., description="Human-readable result message")
    data: Optional[dict] = Field(
        default=None, description="Structured payload (tool-specific)"
    )
