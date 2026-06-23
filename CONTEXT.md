# CONTEXT.md — WeekPilot Engineering & Security Standards
> This file is the project's "constitution." Every contributor and every agent
> must follow these rules. Violations break the build.

## Code Style
- **Formatter:** Black (line-length 100) + isort
- **Linter:** Ruff with security rules enabled (`S`, `B`)
- **Type hints:** Required on ALL function signatures — no exceptions
- **Docstrings:** Required on all public functions and classes (Google style)

## Schemas-First
- Define **Pydantic models** before writing business logic
- Every tool input/output has a typed contract
- No raw dicts crossing module boundaries — use typed models

## Security — Non-Negotiable
- **NO secrets in code.** API keys load from `.env` (local) or Kaggle Secrets
- **All external content is untrusted:** user input, web search results, API
  responses, tool outputs — validate and sanitize everything
- **PII redaction:** Logs, error messages, and agent outputs must never contain
  raw PII (emails, phone numbers, addresses, financial data)
- **Least privilege:** Each agent/tool gets only the permissions it needs
- **Human-in-the-loop:** Required for irreversible actions (delete data, send
  messages, persist sensitive info to long-term memory)
- **Consent-gated memory:** Never auto-persist sensitive data — ask first

## Agent Design
- **Orchestrator pattern:** One root agent routes to domain specialists
- **Single responsibility:** Each sub-agent owns exactly one domain
- **Justify agents:** If a task can be done with a single function call, don't
  make it an agent. Agents exist for reasoning + multi-step tool use
- **Callbacks for guardrails:** Use before/after hooks — not inline checks

## Testing
- **Outcome-based:** Tests assert observable behavior, not implementation details
- **Security tests required:** Every guardrail must have a test proving it blocks
  bad input
- **pass@k:** Evaluate across multiple runs, not one lucky pass

## Git Hygiene
- **Pre-commit hooks:** Secret scanning, linting — must pass before push
- **No large files:** Max 1MB per file in repo
- **Meaningful commits:** One logical change per commit
