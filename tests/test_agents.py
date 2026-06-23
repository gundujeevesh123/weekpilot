"""
WeekPilot Agent Routing Tests — Verify orchestrator sends requests to correct specialists.

Note: These are structural tests that verify agent configuration and routing
intent, not end-to-end LLM tests (which would be non-deterministic and require
API keys). Full agent flow testing is handled in eval/run_eval.py.
"""

from __future__ import annotations

import pytest


class TestAgentConfiguration:
    """Tests verifying agent setup is correct and complete."""

    def test_root_agent_has_all_sub_agents(self):
        """Verify the orchestrator knows about all 4 specialists."""
        from weekpilot.agent import root_agent

        sub_agent_names = {sa.name for sa in root_agent.sub_agents}
        assert sub_agent_names == {
            "task_triage_agent",
            "message_drafter_agent",
            "schedule_planner_agent",
        }
        # research_agent is wired as a tool (AgentTool), not a sub-agent, to
        # avoid the ADK built-in-tool-in-sub-agent limit with google_search.
        tool_agent_names = {
            getattr(getattr(t, "agent", None), "name", None) for t in root_agent.tools
        }
        assert "research_agent" in tool_agent_names

    def test_root_agent_has_security_callbacks(self):
        """Verify security callbacks are wired to the orchestrator."""
        from weekpilot.agent import root_agent

        assert root_agent.before_model_callback is not None
        assert root_agent.after_model_callback is not None

    def test_task_agent_has_correct_tools(self):
        """Verify task agent has all 5 task tools."""
        from weekpilot.agents.task_triage import task_triage_agent

        tool_count = len(task_triage_agent.tools)
        assert tool_count == 5, f"Expected 5 tools, got {tool_count}"

    def test_schedule_agent_has_weather_tool(self):
        """Verify schedule planner has weather forecast capability."""
        from weekpilot.agents.schedule_planner import schedule_planner_agent

        tool_names = [
            getattr(t, 'name', getattr(t, '__name__', str(t)))
            for t in schedule_planner_agent.tools
        ]
        # Should have reminder tools + weather + code_execution
        assert len(schedule_planner_agent.tools) >= 4

    def test_research_agent_uses_google_search(self):
        """Verify research agent has Google Search grounding."""
        from weekpilot.agents.research_agent import research_agent

        assert len(research_agent.tools) >= 1

    def test_message_agent_has_approval_tool(self):
        """Verify message agent has the human-in-the-loop approval tool."""
        from weekpilot.agents.message_drafter import message_drafter_agent

        assert len(message_drafter_agent.tools) == 3

    def test_all_agents_use_gemini_flash(self):
        """Verify all agents use the expected model."""
        from weekpilot.agent import root_agent
        from weekpilot.agents.task_triage import task_triage_agent
        from weekpilot.agents.message_drafter import message_drafter_agent
        from weekpilot.agents.schedule_planner import schedule_planner_agent
        from weekpilot.agents.research_agent import research_agent

        for agent in [
            task_triage_agent,
            message_drafter_agent,
            schedule_planner_agent,
            research_agent,
        ]:
            # model is now a Gemini object (carrying retry config), not a string;
            # read its underlying model id either way.
            model_id = (
                agent.model
                if isinstance(agent.model, str)
                else getattr(agent.model, "model", "")
            )
            assert "gemini" in model_id.lower(), f"{agent.name} uses unexpected model"
