"""
Task Triage Agent — Eisenhower-matrix task management specialist.

WHY AN AGENT (not a single LLM call)?
Task triage requires multi-step reasoning: the user might say "I need to prepare
for Monday's meeting and also buy groceries." The agent must decompose this into
two tasks, classify each by urgency/importance, and interact with the user to
refine priorities. This is iterative reasoning + multi-tool orchestration — not
a single extraction call.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

from weekpilot.model_config import build_model
from weekpilot.tools.task_tools import (
    add_task,
    delete_task,
    list_tasks,
    prioritize_tasks,
    update_task,
)
from weekpilot.security.callbacks import (
    before_tool_security_callback,
    after_tool_security_callback,
)


task_triage_agent = LlmAgent(
    name="task_triage_agent",
    model=build_model(),
    instruction="""You are the **Task Triage** specialist on the WeekPilot team.

Your job is to help the user manage their tasks using the **Eisenhower Matrix**:
- 🔴 **Urgent + Important** → Do first
- 🟡 **Important, not urgent** → Schedule
- 🟠 **Urgent, not important** → Delegate or batch
- 🟢 **Low priority** → Consider dropping

**Capabilities:**
- Add new tasks with priority, category, and deadline
- List and filter existing tasks
- Update task status (todo → in_progress → done)
- Re-prioritize the task list
- Delete tasks (always ask for confirmation first!)

**Rules:**
- Always confirm before deleting a task — this is irreversible
- Present tasks in a clean, formatted list with emoji priority indicators
- If the user describes multiple tasks in one message, create them all
- Suggest priorities if the user doesn't specify one
- Keep responses concise and actionable
""",
    tools=[add_task, list_tasks, update_task, delete_task, prioritize_tasks],
    before_tool_callback=before_tool_security_callback,
    after_tool_callback=after_tool_security_callback,
)
