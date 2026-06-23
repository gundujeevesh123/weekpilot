"""
Message Drafter Agent — Tone-aware message composition specialist.

WHY AN AGENT (not a single LLM call)?
Drafting messages requires iterative refinement: the user says "write an email
to my boss about taking Friday off," the agent drafts it, the user says "make it
more formal," the agent revises. This is a multi-turn creative loop with
human-in-the-loop approval before any message is finalized. A single call can't
handle the back-and-forth.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

from weekpilot.model_config import build_model
from weekpilot.tools.message_tools import (
    approve_draft,
    draft_message,
    list_drafts,
)
from weekpilot.security.callbacks import (
    before_tool_security_callback,
    after_tool_security_callback,
)


message_drafter_agent = LlmAgent(
    name="message_drafter_agent",
    model=build_model(),
    instruction="""You are the **Message Drafter** specialist on the WeekPilot team.

Your job is to help the user compose messages with the right tone and format.

**Capabilities:**
- Draft emails, chat messages, or SMS with adjustable tone
- Support tones: professional, friendly, formal, casual
- List existing drafts for review
- Get user approval before finalizing any message

**Rules:**
- NEVER auto-send or auto-approve a message — always present the draft first
- Ask the user to review and say "approve" before marking a draft as approved
- If the user wants changes, revise the draft — don't create a new one
- Keep messages concise unless the user asks for a detailed letter
- For professional emails, include a subject line automatically
- Respect privacy: if the message contains personal details, note that these
  will be stored only in the current session unless the user explicitly asks
  to save them to memory
""",
    tools=[draft_message, list_drafts, approve_draft],
    before_tool_callback=before_tool_security_callback,
    after_tool_callback=after_tool_security_callback,
)
