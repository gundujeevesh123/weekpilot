"""
WeekPilot Input Validators — shared sanitisation and validation helpers.

Every tool function should run user-supplied values through these helpers
before constructing Pydantic models.  Treat ALL inputs as untrusted.
"""

from __future__ import annotations

import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Allowed enum values (kept in sync with weekpilot.models.schemas)
# ---------------------------------------------------------------------------
ALLOWED_PRIORITIES = {"urgent-important", "important", "urgent", "low"}
ALLOWED_CATEGORIES = {"work", "personal", "health", "errands", "learning"}
ALLOWED_STATUSES = {"todo", "in_progress", "done", "cancelled"}
ALLOWED_REMINDER_STATUSES = {"pending", "triggered", "dismissed"}
ALLOWED_TONES = {"professional", "friendly", "formal", "casual"}
ALLOWED_CHANNELS = {"email", "chat", "sms"}
ALLOWED_DRAFT_STATUSES = {"draft", "approved", "sent"}


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def sanitize_text(text: str, max_length: int = 2000) -> str:
    """Strip control characters (keep newlines/tabs), limit length, and trim.

    Args:
        text: Raw user-supplied string.
        max_length: Maximum allowed length after sanitisation.

    Returns:
        Cleaned string, guaranteed to be at most *max_length* characters.
    """
    if not isinstance(text, str):
        text = str(text)
    # Remove control chars except \n (0x0A) and \t (0x09)
    text = re.sub(r"[^\x09\x0A\x20-\x7E\u00A0-\uFFFF]", "", text)
    text = text.strip()
    return text[:max_length]


# ---------------------------------------------------------------------------
# Date / datetime helpers
# ---------------------------------------------------------------------------

def validate_date(date_str: str) -> bool:
    """Validate a *YYYY-MM-DD* string represents a real calendar date.

    Returns:
        ``True`` when valid, ``False`` otherwise.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def validate_datetime(dt_str: str) -> bool:
    """Validate a *YYYY-MM-DDTHH:MM* string represents a real date-time.

    Returns:
        ``True`` when valid, ``False`` otherwise.
    """
    try:
        datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
        return True
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# City name helper (for weather lookups)
# ---------------------------------------------------------------------------

def sanitize_city_name(city: str) -> str:
    """Allow only alphanumeric characters, spaces, hyphens, and periods.

    Everything else is stripped. Result is capped at 100 characters.

    Args:
        city: Raw city name from the user.

    Returns:
        Sanitised city name ready for the weather API.
    """
    if not isinstance(city, str):
        city = str(city)
    # Keep only alphanumeric, spaces, hyphens, periods
    city = re.sub(r"[^a-zA-Z0-9\s\.\-]", "", city)
    city = city.strip()
    return city[:100]


# ---------------------------------------------------------------------------
# Enum validators
# ---------------------------------------------------------------------------

def validate_priority(priority: str) -> bool:
    """Check *priority* against the Eisenhower-matrix quadrant values."""
    return priority in ALLOWED_PRIORITIES


def validate_category(category: str) -> bool:
    """Check *category* against the allowed task categories."""
    return category in ALLOWED_CATEGORIES
