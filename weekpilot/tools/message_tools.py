"""
WeekPilot Message Tools — draft, list, and approve messages.

All functions receive ``tool_context`` as their first parameter (Google ADK
convention) and read/write ``tool_context.state["drafts"]``.
Return values are plain ``dict``s so ADK can serialise them for the LLM.

A human-in-the-loop step is enforced before a draft can be marked as
"approved" — the LLM must confirm the user's intent first.
"""

from __future__ import annotations

from weekpilot.models.schemas import DraftMessage, ToolResponse
from weekpilot.tools.validators import (
    sanitize_text,
    ALLOWED_TONES,
    ALLOWED_CHANNELS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_draft_state(tool_context) -> list[dict]:
    """Initialise ``state['drafts']`` if it does not exist yet."""
    if "drafts" not in tool_context.state:
        tool_context.state["drafts"] = []
    return tool_context.state["drafts"]


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


def draft_message(
    tool_context,
    recipient: str,
    body: str,
    tone: str = "professional",
    channel: str = "email",
    subject: str = "",
) -> dict:
    """Draft a new message for later approval and sending.

    Use this tool when the user wants to compose, draft, or write a message
    to someone.  The message is saved as a draft and must be explicitly
    approved before it is considered "sent".

    Args:
        tool_context: ADK tool context (auto-injected).
        recipient: Who the message is addressed to.
        body: The message body text.
        tone: Writing tone — 'professional', 'friendly', 'formal', or 'casual'.
        channel: Delivery channel — 'email', 'chat', or 'sms'.
        subject: Optional subject line (primarily for emails).

    Returns:
        dict with status, message, and the created draft data.
    """
    drafts = _ensure_draft_state(tool_context)

    # --- Validate recipient ---
    recipient = sanitize_text(recipient, max_length=200)
    if not recipient:
        return ToolResponse(
            status="error",
            message="Recipient cannot be empty.",
        ).model_dump()

    # --- Validate body ---
    body = sanitize_text(body, max_length=5000)
    if not body:
        return ToolResponse(
            status="error",
            message="Message body cannot be empty.",
        ).model_dump()

    # --- Validate tone ---
    tone = tone.lower().strip()
    if tone not in ALLOWED_TONES:
        return ToolResponse(
            status="error",
            message=f"Invalid tone '{tone}'. Allowed: {sorted(ALLOWED_TONES)}",
        ).model_dump()

    # --- Validate channel ---
    channel = channel.lower().strip()
    if channel not in ALLOWED_CHANNELS:
        return ToolResponse(
            status="error",
            message=f"Invalid channel '{channel}'. Allowed: {sorted(ALLOWED_CHANNELS)}",
        ).model_dump()

    # --- Validate subject ---
    subject_value = None
    if subject:
        subject_value = sanitize_text(subject, max_length=200)

    # --- Build & persist ---
    draft = DraftMessage(
        recipient=recipient,
        body=body,
        tone=tone,
        channel=channel,
        subject=subject_value,
    )
    drafts.append(draft.model_dump())
    tool_context.state["drafts"] = drafts  # write back

    return ToolResponse(
        status="success",
        message=f"Draft message to '{recipient}' created (ID: {draft.id}).",
        data=draft.model_dump(),
    ).model_dump()


def list_drafts(tool_context) -> dict:
    """List all message drafts.

    Use this tool when the user asks to see, list, or review their message
    drafts.

    Args:
        tool_context: ADK tool context (auto-injected).

    Returns:
        dict with status, message, and list of drafts.
    """
    drafts = _ensure_draft_state(tool_context)

    return ToolResponse(
        status="success",
        message=f"Found {len(drafts)} draft(s).",
        data={"drafts": drafts, "total": len(drafts)},
    ).model_dump()


def approve_draft(tool_context, draft_id: str) -> dict:
    """Approve a message draft (human-in-the-loop confirmation).

    This tool marks a draft as 'approved', indicating the user has reviewed
    and confirmed the message.  The first call returns a
    ``confirmation_required`` response; only when the user explicitly
    confirms will the status be changed.

    Use this tool when the user says they want to approve, confirm, or
    send a specific draft.

    Args:
        tool_context: ADK tool context (auto-injected).
        draft_id: The unique draft ID to approve.

    Returns:
        dict with status and message — either confirmation prompt or success.
    """
    drafts = _ensure_draft_state(tool_context)

    draft_id = draft_id.strip()
    if not draft_id:
        return ToolResponse(
            status="error",
            message="Draft ID is required.",
        ).model_dump()

    # Locate the draft
    target = None
    for d in drafts:
        if d.get("id") == draft_id:
            target = d
            break

    if target is None:
        return ToolResponse(
            status="error",
            message=f"No draft found with ID '{draft_id}'.",
        ).model_dump()

    if target.get("status") == "approved":
        return ToolResponse(
            status="success",
            message=f"Draft '{draft_id}' is already approved.",
            data=target,
        ).model_dump()

    # Check for user confirmation flag
    confirmed = tool_context.state.get("draft_approved_confirmed", False)

    if not confirmed:
        return ToolResponse(
            status="confirmation_required",
            message=(
                f"Please confirm you want to approve and send the draft message "
                f"to '{target.get('recipient', 'unknown')}'. "
                f"Subject: '{target.get('subject', '(none)')}'."
            ),
            data=target,
        ).model_dump()

    # User confirmed — mark as approved
    target["status"] = "approved"
    tool_context.state["drafts"] = drafts  # write back
    tool_context.state["draft_approved_confirmed"] = False  # reset flag

    return ToolResponse(
        status="success",
        message=f"Draft '{draft_id}' approved and ready to send.",
        data=target,
    ).model_dump()
