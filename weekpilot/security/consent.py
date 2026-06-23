"""
WeekPilot Consent Gate — consent-gating logic for sensitive data persistence.

Before any PII-bearing payload is written to long-term memory, the system
must obtain explicit user consent.  This module:

* Scans data dicts for sensitive values (via ``pii_detector``).
* Builds a ``ConsentRequest`` when PII is detected.
* Formats a human-readable consent prompt for the user.
* Reads / clears consent state from the agent session state dict.
"""

from __future__ import annotations

from typing import Optional

from weekpilot.models.schemas import ConsentRequest, SensitiveDataFlag
from weekpilot.security.pii_detector import detect_pii

# Keys we write into / read from the agent session state.
_CONSENT_REQUEST_KEY = "pending_consent_request"
_CONSENT_APPROVED_KEY = "pending_consent_approved"

# Human-readable labels for each ``data_type`` value.
_TYPE_LABELS: dict[str, str] = {
    "email": "Email address",
    "phone": "Phone number",
    "address": "Physical address",
    "financial": "Financial data (SSN / credit card)",
    "health": "Health information",
    "name": "Personal name",
}


# =============================================================================
# Public API
# =============================================================================

def check_consent_needed(data: dict) -> Optional[ConsentRequest]:
    """Scan a data dict for PII and return a ``ConsentRequest`` if any is found.

    Each *string* value in *data* is scanned via ``detect_pii``.  Non-string
    values are silently skipped.  The returned ``ConsentRequest`` aggregates
    every detected flag and provides a summary ``data_description``.

    Args:
        data: Arbitrary dictionary whose string values should be checked.

    Returns:
        A ``ConsentRequest`` describing the detected sensitive data, or
        ``None`` if no PII was found.

    Example::

        >>> req = check_consent_needed({"recipient": "alice@example.com"})
        >>> req is not None
        True
        >>> req.sensitive_fields[0].data_type
        'email'
    """
    all_flags: list[SensitiveDataFlag] = []

    for field_name, value in data.items():
        if not isinstance(value, str):
            continue
        flags = detect_pii(value)
        # Override generic ``field_name`` with the actual dict key.
        for flag in flags:
            flag.field_name = field_name
        all_flags.extend(flags)

    if not all_flags:
        return None

    # Build a human-readable description summarising what was found.
    unique_types = sorted({f.data_type for f in all_flags})
    type_summary = ", ".join(_TYPE_LABELS.get(t, t) for t in unique_types)
    description = (
        f"Detected sensitive data ({type_summary}) in the provided information. "
        "User consent is required before this data can be persisted."
    )

    return ConsentRequest(
        data_description=description,
        sensitive_fields=all_flags,
        approved=None,  # pending
    )


def format_consent_prompt(request: ConsentRequest) -> str:
    """Format a ``ConsentRequest`` into a human-readable prompt.

    Args:
        request: The consent request to format.

    Returns:
        A multi-line string ready to be shown to the user.

    Example::

        >>> prompt = format_consent_prompt(request)
        >>> print(prompt)
        ⚠️ I detected sensitive data:
        - Email address in "recipient"
        ...
    """
    lines: list[str] = ["⚠️ I detected sensitive data:"]
    for flag in request.sensitive_fields:
        label = _TYPE_LABELS.get(flag.data_type, flag.data_type)
        lines.append(f"- {label} in \"{flag.field_name}\"")

    lines.append("")
    lines.append("May I save this to long-term memory? (yes/no)")
    return "\n".join(lines)


def is_consent_granted(state: dict) -> bool:
    """Check whether user consent has been granted.

    Args:
        state: The agent session state dictionary.

    Returns:
        ``True`` if ``state['pending_consent_approved']`` is ``True``,
        ``False`` otherwise (including if the key is missing).
    """
    return state.get(_CONSENT_APPROVED_KEY) is True


def clear_consent_state(state: dict) -> None:
    """Remove all consent-related keys from the session state.

    Args:
        state: The agent session state dictionary (modified in-place).
    """
    state.pop(_CONSENT_REQUEST_KEY, None)
    state.pop(_CONSENT_APPROVED_KEY, None)
