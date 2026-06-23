"""
WeekPilot Root Agent — The Orchestrator.

This is the ADK entry point. It exports `root_agent` which ADK discovers
and uses as the primary agent. The orchestrator routes user requests to the
appropriate specialist sub-agent based on intent.

Architecture rationale:
- The orchestrator uses LLM-based routing (not keyword matching) because
  user requests are often ambiguous: "help me prepare for Monday" could be
  task management, schedule planning, or research depending on context.
- Each sub-agent has focused instructions and a limited tool set, following
  the principle of least privilege and single responsibility.
- Security callbacks are applied at the orchestrator level to catch threats
  before they reach any sub-agent.
"""

from __future__ import annotations

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from weekpilot.model_config import build_model

from weekpilot.agents.task_triage import task_triage_agent
from weekpilot.agents.message_drafter import message_drafter_agent
from weekpilot.agents.schedule_planner import schedule_planner_agent
from weekpilot.agents.research_agent import research_agent
from weekpilot.security.callbacks import (
    before_model_security_callback,
    after_model_security_callback,
)

# Load environment variables from .env (local dev) — on Kaggle, use Secrets
load_dotenv()

# ─── Root Agent (Orchestrator) ────────────────────────────────────────────────

root_agent = Agent(
    name="weekpilot",
    model=build_model(),
    instruction="""You are **WeekPilot** 🚀, a privacy-first weekly planning concierge.

You coordinate a team of specialists to help the user plan their week effectively.

**Your team:**
- 📋 **task_triage_agent** — Manages tasks (add, list, update, prioritize, delete)
- ✉️ **message_drafter_agent** — Drafts messages (email, chat, SMS) with tone control
- 📅 **schedule_planner_agent** — Plans weekly schedules, checks weather, sets reminders
- 🔍 **research_agent** — Searches the web for information (meeting prep, locations, etc.)

**Routing rules:**
- Task-related requests (add/manage/prioritize tasks) → transfer to **task_triage_agent**
- Message writing requests → transfer to **message_drafter_agent**
- Scheduling, calendar, reminders, weather → transfer to **schedule_planner_agent**
- Information lookup, research, web search → use the **research_agent** tool (call it directly; do not transfer)
- Multi-domain requests: handle the primary intent first, then address secondary needs

**Privacy rules (non-negotiable):**
- NEVER auto-persist sensitive personal data — always ask for consent first
- If the user shares PII (email, phone, address), acknowledge it but flag that
  it will only be stored if they explicitly approve
- Keep all personal data within the session unless the user opts into long-term memory
- Never include user's personal data in web searches or API calls

**Personality:**
- Friendly, efficient, and organized
- Use clear formatting with headers, bullet points, and emoji indicators
- Give proactive suggestions ("Would you also like me to set a reminder for that?")
- Keep responses concise — the user is busy and planning, not chatting
""",
    sub_agents=[
        task_triage_agent,
        message_drafter_agent,
        schedule_planner_agent,
    ],
    # research_agent is exposed as a TOOL (not a sub-agent) so its built-in
    # google_search works: ADK forbids transferring into a sub-agent that then
    # uses a built-in tool in the same turn. AgentTool sidesteps that cleanly.
    tools=[AgentTool(agent=research_agent)],
    before_model_callback=before_model_security_callback,
    after_model_callback=after_model_security_callback,
)
