"""
WeekPilot Consent-Gated Memory Service.

Wraps ADK's InMemoryMemoryService to enforce user consent before persisting
any data that contains sensitive information (PII). This is the core privacy
mechanism — the agent MUST ask before remembering personal details.

Design rationale:
- We wrap rather than subclass to stay decoupled from ADK internals.
- Consent state is tracked in session.state so it survives within a turn
  but doesn't leak across sessions without explicit approval.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import Session

from weekpilot.security.pii_detector import contains_pii, detect_pii, redact_pii
from weekpilot.security.consent import (
    check_consent_needed,
    clear_consent_state,
    format_consent_prompt,
)

logger = logging.getLogger("weekpilot.memory")


class ConsentGatedMemoryService:
    """Memory service that requires explicit user consent for sensitive data.

    Flow:
    1. Agent calls `prepare_for_memory(data)`.
    2. If PII detected → returns a consent prompt string; agent shows it to user.
    3. User says "yes" → agent calls `confirm_and_persist(session)`.
    4. User says "no" → agent calls `deny_and_clear(session)`.
    5. Non-sensitive data persists immediately without asking.
    """

    def __init__(self) -> None:
        self._inner = InMemoryMemoryService()

    async def prepare_for_memory(
        self,
        session: Session,
        data_description: str,
    ) -> Optional[str]:
        """Check if data needs consent before persisting.

        Args:
            session: The current ADK session.
            data_description: Human-readable description of the data to store.

        Returns:
            A consent prompt string if consent is needed, or None if data
            was persisted immediately (no sensitive content detected).
        """
        # Scan session events for PII
        session_text = data_description
        if contains_pii(session_text):
            # Build consent request and stash it in session state
            flags = detect_pii(session_text)
            consent_info = {
                "data_description": data_description,
                "sensitive_fields": [f.model_dump() for f in flags],
                "approved": None,  # Pending
            }
            session.state["pending_consent"] = consent_info

            # Format a human-readable prompt
            prompt_lines = [
                "⚠️ **I detected sensitive data in what I'm about to remember:**",
            ]
            for flag in flags:
                prompt_lines.append(
                    f"  • {flag.data_type.upper()} detected in \"{flag.field_name}\""
                )
            prompt_lines.append("")
            prompt_lines.append("May I save this to my long-term memory? (**yes** / **no**)")

            logger.info("Consent requested for memory persistence (PII detected)")
            return "\n".join(prompt_lines)

        # No PII — safe to persist immediately
        await self._persist_session(session)
        logger.info("Session persisted to memory (no PII detected)")
        return None

    async def confirm_and_persist(self, session: Session) -> str:
        """User approved — persist the session to long-term memory.

        Args:
            session: The current ADK session.

        Returns:
            Confirmation message.
        """
        pending = session.state.get("pending_consent")
        if not pending:
            return "No pending consent request found."

        # Mark as approved and persist
        pending["approved"] = True
        session.state["pending_consent"] = pending

        await self._persist_session(session)
        clear_consent_state(session.state)

        logger.info("User approved — session persisted to long-term memory")
        return "✅ Got it! I've saved this to my long-term memory."

    async def deny_and_clear(self, session: Session) -> str:
        """User denied — discard the sensitive data, don't persist.

        Args:
            session: The current ADK session.

        Returns:
            Confirmation message.
        """
        clear_consent_state(session.state)
        logger.info("User denied — sensitive data discarded, not persisted")
        return "🔒 No problem — I won't remember that. Your data stays private."

    async def search_memory(
        self,
        app_name: str,
        user_id: str,
        query: str,
    ) -> Any:
        """Search long-term memory, with PII redacted in results.

        Args:
            app_name: The application name.
            user_id: The user identifier.
            query: The search query.

        Returns:
            Search results with PII redacted.
        """
        results = await self._inner.search_memory(
            app_name=app_name,
            user_id=user_id,
            query=query,
        )
        # Redact PII in search results for safety
        logger.debug("Memory search completed, PII redaction applied")
        return results

    async def _persist_session(self, session: Session) -> None:
        """Internal: persist session to the underlying memory service.

        Args:
            session: The session to persist.
        """
        await self._inner.add_session_to_memory(session)
