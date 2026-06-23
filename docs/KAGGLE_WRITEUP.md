# WeekPilot — Kaggle Capstone Write-Up

## The Problem: Weekly Planning Is Fragmented and Privacy-Hostile

Modern professionals manage their weeks across a dozen apps: to-do lists,
email clients, calendar tools, weather apps, and search engines. Each
interaction is siloed, and most AI assistants quietly collect personal data
without explicit consent.

**Who it helps:** Busy professionals, students, and freelancers who want a
single AI assistant to plan their week — without surrendering their privacy.

**The gap:** No existing tool combines task prioritization, message drafting,
weather-aware scheduling, and contextual research in one privacy-respecting
agent system.

---

## Why an Agentic Approach?

A single LLM prompt can answer questions, but it can't:

1. **Route intent** — "Help me prepare for Monday's meeting" could mean
   creating tasks, drafting emails, or researching the topic. An orchestrator
   agent classifies intent and delegates to the right specialist.

2. **Use domain-specific tools** — Each planning domain requires different
   tools (task CRUD, weather APIs, Google Search). Separate agents keep tool
   sets focused and follow least-privilege.

3. **Enforce human-in-the-loop** — A monolithic system can't easily enforce
   that messages need approval or sensitive data needs consent. Individual
   agents encode these rules in their instructions and tools.

4. **Maintain context across domains** — Session state shared via the
   orchestrator allows the schedule planner to read tasks and the message
   drafter to reference upcoming meetings.

WeekPilot uses agents because the problem is genuinely multi-domain,
multi-step, and requires iterative human interaction.

---

## Architecture

WeekPilot follows the **Orchestrator + Specialists** pattern:

- **WeekPilot Orchestrator** (`root_agent`) — LLM-based intent classification
  that routes to the appropriate specialist via ADK's `transfer_to` mechanism.

- **Task Triage Agent** — Manages tasks using the Eisenhower matrix
  (urgent/important). 5 custom tools for CRUD + prioritization.

- **Message Drafter Agent** — Composes tone-aware messages (professional,
  friendly, formal, casual) across email/chat/SMS. Human-in-the-loop
  approval before any message is finalized.

- **Schedule Planner Agent** — Plans the week with time-blocking, integrates
  weather forecasts via wttr.in REST API, and uses code execution for time
  calculations.

- **Research Agent** — Google Search-grounded information gathering for
  meeting prep, location lookup, and contextual research.

All agents share session state for cross-domain coordination and are wrapped
in security callbacks for input validation, output scanning, and PII redaction.

---

## Tools, Memory, and Security

### Tools (14 total)
- **Custom Function Tools (12):** Task CRUD (5), Reminder management (3),
  Message drafting (3), Weather forecast (1)
- **Built-in Tools (2):** Google Search grounding, Code Execution
- **External REST API (1):** wttr.in weather service (free, no key required)

### Memory
- **Session State:** Current conversation context (tasks, reminders, drafts)
- **Long-Term Memory:** Consent-gated — PII is detected automatically, and
  the agent explicitly asks for user permission before persisting anything
  sensitive.

### Security (CIA Triad)
- **Confidentiality:** PII redaction in logs/outputs, consent-gated memory,
  zero hardcoded secrets, output scanning for leaked keys
- **Integrity:** Input validation, prompt injection blocking, tool allow-listing,
  schema validation on all data
- **Availability:** Input size limits, API timeouts, graceful error handling

Full STRIDE threat model documented in `STRIDE.md`.

---

## Results and Evaluation

### Structural Tests (No API Key Required)
- 7/7 structural validation checks pass
- Agent configuration verified: 4 sub-agents, 12+ tools, security callbacks wired

### Security Tests
- PII detection: catches email, phone, SSN patterns; no false positives on clean text
- Guardrails: blocks prompt injection (3 attack patterns tested), allows legitimate input
- Tool allow-listing: blocks unauthorized tools, allows listed tools
- Consent gating: triggers on PII, skips on clean data, clears state properly
- Output scanning: redacts Google API keys, OpenAI keys from responses

### Evaluation Suite
- 10 rubric-style eval cases covering: task management, scheduling, message drafting,
  research, prompt injection defense, PII consent, multi-domain requests, error handling
- pass@k measured across 3 runs per case

---

## Limitations and Future Work

**Current limitations:**
- Weather data limited to wttr.in (3-day forecast, basic conditions)
- Long-term memory uses in-memory storage (lost on restart) — production would
  use Firestore or a vector DB
- No calendar API integration (Google Calendar is a natural extension)
- Evaluation uses heuristic scoring — LLM-as-judge would be more robust

**Future extensions:**
- Google Calendar integration for real scheduling
- Email API integration for actual message sending (with consent)
- Voice interface via Gemini multimodal
- Deployment to Google Cloud Run for persistent availability
- Multi-user support with per-user memory isolation

---

## Code Link

🔗 [GitHub Repository](https://github.com/YOUR_USERNAME/weekpilot)

---

*Built for the Google × Kaggle AI Agents Intensive (Vibe Coding) Capstone.*
*Licensed under CC-BY 4.0.*
