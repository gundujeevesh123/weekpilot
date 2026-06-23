"""
WeekPilot PII Detector — regex-based detection and redaction of personally
identifiable information (PII).

All patterns are pre-compiled for performance.  The detector scans free-text
for common PII types (email, phone, SSN, credit card) and can either flag
matches as ``SensitiveDataFlag`` objects or redact them in-place.

Design notes
------------
* Patterns deliberately favour *recall* over *precision* — a false-positive
  that gets redacted is far less harmful than a leaked SSN.
* Credit-card detection uses a simple 16-digit heuristic; Luhn validation is
  intentionally omitted to keep this module dependency-free.
"""

from __future__ import annotations

import re
from typing import List

from weekpilot.models.schemas import SensitiveDataFlag

# =============================================================================
# Compiled regex patterns (module-level for performance)
# =============================================================================

# RFC-5322-ish email — good enough for scanning, not for formal validation.
_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

# US phone: (xxx) xxx-xxxx, xxx-xxx-xxxx, +1xxxxxxxxxx, etc.
# International: +<country-code> with 7-15 digits and optional separators.
_PHONE_RE = re.compile(
    r"(?<!\d)"                      # not preceded by another digit
    r"(?:"
    r"\+?1[\s.\-]?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}"  # US variants
    r"|"
    r"\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}"                 # (xxx) xxx-xxxx
    r"|"
    r"\+\d{1,3}[\s.\-]?\d{4,14}"                            # international
    r")"
    r"(?!\d)",                       # not followed by another digit
)

# US Social Security Number: XXX-XX-XXXX (with dashes required to reduce FPs).
_SSN_RE = re.compile(
    r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)",
)

# Credit-card number: 16 digits with optional spaces / dashes between groups.
_CC_RE = re.compile(
    r"(?<!\d)"
    r"\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}"
    r"(?!\d)",
)

# Master mapping: pattern → (data_type for schema, redaction placeholder)
_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (_EMAIL_RE, "email",     "[REDACTED-EMAIL]"),
    (_SSN_RE,   "financial", "[REDACTED-SSN]"),
    (_CC_RE,    "financial", "[REDACTED-CC]"),
    (_PHONE_RE, "phone",     "[REDACTED-PHONE]"),
]


# =============================================================================
# Public API
# =============================================================================

def detect_pii(text: str) -> List[SensitiveDataFlag]:
    """Scan *text* for PII and return a list of detection flags.

    Args:
        text: Free-form string to scan.

    Returns:
        A list of ``SensitiveDataFlag`` objects, one per match.  The
        ``value_preview`` is limited to the first 3 visible characters
        followed by ``***`` to prevent leaking the full value.

    Example::

        >>> flags = detect_pii("Contact me at jane@example.com")
        >>> flags[0].data_type
        'email'
    """
    flags: list[SensitiveDataFlag] = []
    for pattern, data_type, _placeholder in _PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group()
            # Build a safe preview: show up to 3 chars then mask the rest.
            preview = raw[:3] + "***" if len(raw) > 3 else "[REDACTED]"
            flags.append(
                SensitiveDataFlag(
                    field_name="text",
                    data_type=data_type,
                    value_preview=preview,
                    requires_consent=True,
                )
            )
    return flags


def redact_pii(text: str) -> str:
    """Replace every detected PII occurrence with a tagged placeholder.

    Args:
        text: Free-form string potentially containing PII.

    Returns:
        A copy of *text* with PII replaced by ``[REDACTED-<TYPE>]`` tokens.

    Example::

        >>> redact_pii("Call 555-123-4567 or email me@x.com")
        'Call [REDACTED-PHONE] or email [REDACTED-EMAIL]'
    """
    result = text
    for pattern, _data_type, placeholder in _PATTERNS:
        result = pattern.sub(placeholder, result)
    return result


def contains_pii(text: str) -> bool:
    """Quick boolean check for the presence of any PII in *text*.

    Args:
        text: Free-form string to scan.

    Returns:
        ``True`` if at least one PII pattern matches, ``False`` otherwise.
    """
    for pattern, _data_type, _placeholder in _PATTERNS:
        if pattern.search(text):
            return True
    return False
