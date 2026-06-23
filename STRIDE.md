# STRIDE Threat Model — WeekPilot

> Generated for the WeekPilot privacy-first weekly concierge agent.
> Last updated: 2026-06-23

## Architecture Overview

WeekPilot processes user text via an LLM orchestrator that routes to 4 specialist
sub-agents. Data flows: User → Orchestrator → Sub-agent → Tools → External APIs.
All personal data stays in session/memory; only sanitized queries go to external APIs.

---

## Threat Analysis

### S — Spoofing

| # | Threat | Risk | Mitigation |
|---|--------|------|------------|
| S1 | Malicious web content impersonates a trusted source via Google Search results | Medium | Research agent treats ALL web content as untrusted; anti-injection in system prompt |
| S2 | Forged tool responses from external APIs | Low | Weather API responses validated against expected schema; no executable content accepted |

### T — Tampering

| # | Threat | Risk | Mitigation |
|---|--------|------|------------|
| T1 | Prompt injection via task descriptions to alter agent behavior | High | Input sanitization via `validate_input()`, blocked injection patterns, before_model callback |
| T2 | Manipulated weather API responses to influence scheduling | Low | Response schema validation; weather data treated as advisory, not authoritative |
| T3 | Tampering with session state to bypass consent | Medium | Consent state keys are managed only by consent module; no direct user manipulation path |

### R — Repudiation

| # | Threat | Risk | Mitigation |
|---|--------|------|------------|
| R1 | Agent takes action without audit trail | Medium | Structured JSON logging of all agent decisions, tool calls, and routing (PII-redacted) |
| R2 | User denies approving a message draft | Low | Approval tool creates audit entry in session state with timestamp |

### I — Information Disclosure

| # | Threat | Risk | Mitigation |
|---|--------|------|------------|
| I1 | PII leakage in logs, error messages, or agent responses | High | PII detection + redaction in after_model callback and log formatter |
| I2 | API key leakage in code, logs, or responses | Critical | Zero hardcoded secrets; .env only; pre-commit secret scanning; output scanning for key patterns |
| I3 | Personal data sent to weather API | Medium | City names sanitized; no personal data included in API requests |
| I4 | System prompt disclosure via prompt injection | High | Injection pattern blocking; anti-disclosure instructions in system prompt |

### D — Denial of Service

| # | Threat | Risk | Mitigation |
|---|--------|------|------------|
| D1 | Oversized input to exhaust context window | Medium | MAX_INPUT_LENGTH=2000 enforced in before_model callback |
| D2 | Rapid API calls to weather endpoint | Low | Single call per request; 5-second timeout; graceful fallback on failure |
| D3 | Infinite agent routing loops | Low | ADK's built-in transfer limits; finite sub-agent set |

### E — Elevation of Privilege

| # | Threat | Risk | Mitigation |
|---|--------|------|------------|
| E1 | Tool abuse — calling unauthorized tools | High | ALLOWED_TOOLS allow-list enforced in before_tool callback; unknown tools blocked |
| E2 | Agent autonomously persisting sensitive data | High | Consent-gated memory; explicit user approval required before any PII persistence |
| E3 | Message auto-sending without user review | Medium | Human-in-the-loop approval required for message drafts; no auto-send capability |
| E4 | Task deletion without confirmation | Medium | delete_task returns confirmation_required; requires explicit user approval |

---

## Mitigation Summary

| Control | Implementation | File |
|---------|---------------|------|
| Input sanitization | `validate_input()` + `sanitize_text()` | `security/guardrails.py`, `tools/validators.py` |
| Prompt injection blocking | Blocked patterns regex + system prompt hardening | `security/guardrails.py`, `security/callbacks.py` |
| Tool allow-listing | `ALLOWED_TOOLS` set checked in `before_tool_callback` | `security/guardrails.py`, `security/callbacks.py` |
| PII detection & redaction | Compiled regex patterns for email, phone, SSN, CC | `security/pii_detector.py` |
| Output scanning | Secret pattern detection in LLM output | `security/guardrails.py` |
| Consent gating | Detect → Ask → Persist only on approval | `security/consent.py`, `memory/consent_memory.py` |
| Human-in-the-loop | Required for delete, approve, persist sensitive | Tools + agent instructions |
| Secret management | `.env` only; `.gitignore` blocks `.env`; pre-commit hooks | `.env.example`, `.gitignore`, `.pre-commit-config.yaml` |
| Structured logging | JSON format with PII redaction | `observability/logger.py` |
| Audit trail | All tool calls and routing decisions logged | `security/callbacks.py` |
