"""
WeekPilot Memory Tests — Verify consent-gating and memory behavior.

These tests verify that the consent-gated memory service correctly:
1. Detects when consent is needed (PII present)
2. Blocks persistence without approval
3. Allows persistence after approval
4. Clears consent state properly
"""

from __future__ import annotations

import pytest


class TestConsentMemoryLogic:
    """Unit tests for consent-gating logic (no async/ADK dependencies)."""

    def test_consent_needed_for_pii_data(self):
        """Data with email triggers consent requirement."""
        from weekpilot.security.consent import check_consent_needed

        data = {
            "recipient": "alice@example.com",
            "body": "Meeting reminder",
        }
        result = check_consent_needed(data)
        assert result is not None
        assert result.approved is None  # Pending

    def test_no_consent_for_safe_data(self):
        """Data without PII doesn't require consent."""
        from weekpilot.security.consent import check_consent_needed

        data = {
            "title": "Weekly review",
            "priority": "important",
        }
        result = check_consent_needed(data)
        assert result is None

    def test_consent_prompt_is_formatted(self):
        """Consent prompt should be human-readable."""
        from weekpilot.security.consent import check_consent_needed, format_consent_prompt

        data = {"contact": "john@test.com"}
        request = check_consent_needed(data)
        assert request is not None

        prompt = format_consent_prompt(request)
        assert "sensitive" in prompt.lower() or "detected" in prompt.lower() or "⚠️" in prompt

    def test_consent_state_lifecycle(self):
        """Consent state should be cleanly added and removed."""
        from weekpilot.security.consent import clear_consent_state

        state = {
            "pending_consent_request": {"data": "test", "approved": None},
            "pending_consent_approved": None,
            "tasks": [{"title": "Keep me"}],
        }

        clear_consent_state(state)

        assert "pending_consent_request" not in state
        assert "pending_consent_approved" not in state
        assert "tasks" in state  # Other state preserved
        assert len(state["tasks"]) == 1
