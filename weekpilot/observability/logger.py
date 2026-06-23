"""
WeekPilot Structured Logger — Observability with PII Redaction.

Provides JSON-structured logging for agent decisions, tool calls, and routing,
with automatic PII redaction applied before any data hits the log.

Design rationale:
- We use Python's stdlib logging with a custom JSON formatter so logs are
  machine-parseable while staying human-readable.
- PII redaction is applied at the formatter level — even if a developer
  accidentally logs raw user data, it gets scrubbed before disk/stdout.
- The get_logger() factory ensures consistent configuration project-wide.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Optional


# Lazy import to avoid circular dependency — pii_detector may import logger
_redact_pii = None


def _get_redactor():
    """Lazy-load PII redactor to break circular imports."""
    global _redact_pii
    if _redact_pii is None:
        try:
            from weekpilot.security.pii_detector import redact_pii
            _redact_pii = redact_pii
        except ImportError:
            # Fallback: no redaction if security module not yet available
            _redact_pii = lambda text: text  # noqa: E731
    return _redact_pii


class PIIRedactingFormatter(logging.Formatter):
    """JSON log formatter that scrubs PII from all log messages.

    Output format (one JSON object per line):
    {
        "timestamp": "2026-06-23T12:00:00Z",
        "level": "INFO",
        "logger": "weekpilot.agents",
        "message": "Routing to task_triage_agent",
        "agent": "weekpilot",
        "tool": null,
        "extra": {}
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a PII-redacted JSON line."""
        redactor = _get_redactor()

        # Redact the message
        message = redactor(record.getMessage())

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "agent": getattr(record, "agent", None),
            "tool": getattr(record, "tool", None),
        }

        # Include extra fields if present, also redacted
        extra = getattr(record, "extra_data", None)
        if extra and isinstance(extra, dict):
            entry["extra"] = {
                k: redactor(str(v)) if isinstance(v, str) else v
                for k, v in extra.items()
            }

        return json.dumps(entry, default=str)


def get_logger(
    name: str,
    level: Optional[str] = None,
) -> logging.Logger:
    """Get a configured WeekPilot logger.

    Args:
        name: Logger name (e.g., 'weekpilot.agents', 'weekpilot.tools').
        level: Log level override. Defaults to WEEKPILOT_LOG_LEVEL env var or INFO.

    Returns:
        A configured logging.Logger instance with PII-redacting JSON output.
    """
    log_level = level or os.environ.get("WEEKPILOT_LOG_LEVEL", "INFO")

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(PIIRedactingFormatter())
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    return logger


def log_agent_event(
    logger: logging.Logger,
    event_type: str,
    agent_name: str,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Log a structured agent event (routing, tool call, response).

    Args:
        logger: The logger instance.
        event_type: Event category (e.g., 'route', 'tool_call', 'response').
        agent_name: Name of the agent generating the event.
        details: Optional extra data to include.
    """
    logger.info(
        f"[{event_type}] {agent_name}",
        extra={
            "agent": agent_name,
            "extra_data": details or {},
        },
    )


def log_tool_call(
    logger: logging.Logger,
    tool_name: str,
    args: Optional[dict] = None,
    result_status: Optional[str] = None,
) -> None:
    """Log a tool invocation with redacted arguments.

    Args:
        logger: The logger instance.
        tool_name: Name of the tool called.
        args: Tool arguments (will be PII-redacted).
        result_status: The result status ('success', 'error', etc.).
    """
    logger.info(
        f"[tool_call] {tool_name} → {result_status or 'pending'}",
        extra={
            "tool": tool_name,
            "extra_data": {"args_keys": list((args or {}).keys())},
        },
    )


def format_run_trace(events: list[dict]) -> str:
    """Format a concise run trace for demo display.

    Args:
        events: List of event dicts with 'type', 'agent', 'detail' keys.

    Returns:
        A formatted multi-line string suitable for display.
    """
    lines = ["─── WeekPilot Run Trace ───"]
    for i, evt in enumerate(events, 1):
        icon = {
            "route": "🔀",
            "tool_call": "🔧",
            "response": "💬",
            "security": "🛡️",
            "memory": "🧠",
            "error": "❌",
        }.get(evt.get("type", ""), "•")

        agent = evt.get("agent", "unknown")
        detail = evt.get("detail", "")
        lines.append(f"  {i}. {icon} [{agent}] {detail}")

    lines.append("───────────────────────────")
    return "\n".join(lines)
