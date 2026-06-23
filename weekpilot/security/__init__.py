"""
WeekPilot Security Layer — package initializer.

Re-exports key security functions so callers can do:
    from weekpilot.security import detect_pii, validate_input, ...
"""

from __future__ import annotations

from weekpilot.security.pii_detector import contains_pii, detect_pii, redact_pii
from weekpilot.security.guardrails import is_tool_allowed, validate_input, validate_output
from weekpilot.security.consent import (
    check_consent_needed,
    clear_consent_state,
    format_consent_prompt,
    is_consent_granted,
)
from weekpilot.security.callbacks import (
    after_model_security_callback,
    after_tool_security_callback,
    before_model_security_callback,
    before_tool_security_callback,
)

__all__ = [
    # PII detection
    "detect_pii",
    "redact_pii",
    "contains_pii",
    # Guardrails
    "validate_input",
    "is_tool_allowed",
    "validate_output",
    # Consent
    "check_consent_needed",
    "format_consent_prompt",
    "is_consent_granted",
    "clear_consent_state",
    # ADK callbacks
    "before_model_security_callback",
    "after_model_security_callback",
    "before_tool_security_callback",
    "after_tool_security_callback",
]
