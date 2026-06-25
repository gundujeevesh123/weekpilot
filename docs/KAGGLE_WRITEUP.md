# WeekPilot — Plan your week in one sentence, keep your data private

**Subtitle:** A privacy‑first, multi‑agent weekly concierge built on Google's
Agent Development Kit and Gemini — with a Model Context Protocol server, a
security layer that's coded in (not bolted on), and a clean React web app.

**Track:** Concierge Agents

---

## The problem

Every week, most of us run our lives across half a dozen tools: a to‑do list, an
email client, a calendar, a weather app, and a search engine. The work of
*planning* — deciding what matters, blocking time, drafting the message, checking
if it'll rain — is fragmented and manual. And the AI assistants that promise to
help usually do it by quietly collecting personal data.

WeekPilot is for busy professionals, students, and freelancers who want **one**
friendly assistant to plan their whole week — without surrendering their privacy.
The gap it fills: no single tool combines task prioritization, weather‑aware
scheduling, message drafting, and research in one place *and* treats your
personal data as yours by default.

## Why an agent (and not just a prompt)

A single LLM call can answer a question, but weekly planning is genuinely
multi‑step and multi‑domain. "Help me get ready for Monday" might mean creating
tasks, drafting an email, or researching a venue. WeekPilot uses an agentic
design because it needs to:

- **Route intent** — an orchestrator reads the request and delegates to the right
  specialist instead of guessing with one giant prompt.
- **Use focused tools** — each domain needs different tools (task CRUD, weather,
  search). Separate agents keep tool sets small and follow least privilege.
- **Keep a human in the loop** — messages are drafted, never auto‑sent; sensitive
  data is never stored without explicit consent.
- **Share context** — agents read a shared session so the planner can see your
  tasks and the drafter can reference your week.

## What WeekPilot does

You type a plain sentence — *"Plan my week in London: gym Mon/Wed/Fri 7am,
deep‑work mornings, dinner with Sam Friday — check the weather"* — and WeekPilot
returns a time‑blocked week, weather‑aware, with reminders set. You can ask it to
triage and prioritize tasks (Eisenhower matrix), draft a tone‑aware email for your
approval, or research a venue. And if you ever mention something personal — say,
a doctor's email — it pauses and *asks* before remembering it.

## Architecture

WeekPilot follows an **orchestrator + specialists** pattern on Google's Agent
Development Kit (ADK), powered by Gemini (2.5 Flash by default, configurable in
one place).

- **Orchestrator (`root_agent`)** — LLM‑based intent routing to the right
  specialist, with security callbacks applied before any sub‑agent is reached.
- **Task Triage agent** — task CRUD + prioritization with the Eisenhower matrix.
- **Schedule Planner agent** — weekly time‑blocking, weather, and reminders.
- **Message Drafter agent** — tone‑aware email/chat/SMS drafts with human approval.
- **Research agent** — Google Search–grounded lookups, exposed to the orchestrator
  as an **AgentTool** (this deliberately sidesteps an ADK limitation where a
  built‑in tool like `google_search` can't run inside a transferred sub‑agent).

The "world" tools — **weather and current date/time** — are served by a dedicated
**MCP (Model Context Protocol) server** over a local stdio transport. The
Schedule Planner consumes them through ADK's `McpToolset` with a `tool_filter`
(least privilege). Crucially, this server only ever sees **public data** (a city
name, a timezone) — your tasks, reminders, messages, and any PII never cross that
boundary. The privacy promise is enforced by the architecture itself.

On top of the agent sits a small **web app**: a React + Vite + TypeScript
front‑end talking to a thin **FastAPI** backend that wraps the ADK runner. The
Gemini API key stays server‑side and never reaches the browser.

## Course concepts demonstrated

The capstone asks for at least three course concepts. WeekPilot demonstrates four,
three of them in code:

1. **Multi‑agent system (ADK)** — an orchestrator coordinating four specialists.
2. **MCP server** — `weekpilot/mcp_server/` exposes public‑data tools over stdio,
   consumed via `McpToolset`.
3. **Security features** — four ADK callbacks, consent‑gated memory, PII
   redaction, input/output guardrails, and a STRIDE threat model.
4. **Deployability** — a runnable web app, one‑command setup, pinned dependencies,
   and a documented Cloud Run / Firebase deployment path.

## Security and privacy by design

Security is implemented as code, mapped to the classic CIA triad:

- **Confidentiality** — PII is detected and redacted from logs and outputs;
  long‑term memory is consent‑gated (the agent asks before remembering anything
  sensitive); there are zero hardcoded secrets (the key loads from a git‑ignored
  `.env`); outputs are scanned for leaked API keys; and the MCP boundary keeps
  personal data out of external tool calls. In the web app, the key is
  server‑side only and CORS is locked to explicit origins.
- **Integrity** — all input is validated and length‑limited; prompt‑injection
  patterns are blocked; tools are allow‑listed (only approved tools run); and
  every cross‑module payload is a typed Pydantic model.
- **Availability** — input size limits, API timeouts, graceful error handling, and
  **automatic retry with exponential backoff** on transient Gemini `429/5xx`
  responses, so a momentary overload self‑heals instead of failing the user.

Every guardrail has a test that proves it works — prompt injection is blocked,
PII is redacted, unauthorized tools are denied, and Google/OpenAI key patterns
are scrubbed from output.

## The build and the journey

The project started as an ADK agent and grew into a small product. Three moments
stand out:

- **A bug that looked scary but was simple.** Early on, planning a schedule threw
  "a bunch of file errors." It turned out the tool‑callback signatures didn't
  match ADK's contract, so the framework raised a `TypeError` the moment any tool
  ran — a multi‑line traceback that *looked* like file errors. Aligning the
  callbacks to ADK's `(tool, args, tool_context[, tool_response])` shape fixed it,
  and a regression test now guards it.
- **Adding the MCP server.** To demonstrate the Model Context Protocol cleanly —
  and to harden the privacy story — the weather and date tools moved behind a
  stdio MCP server that only handles public data.
- **From dev UI to a real app.** A `503 (model overloaded)` during a demo wasn't a
  bug — it was Gemini under load. That prompted a centralized model config with
  automatic retry, and a polished React + FastAPI web app so the experience feels
  like a product, not a developer tool.

Tooling: Google ADK, Gemini, the MCP Python SDK, FastAPI/Uvicorn, React + Vite +
TypeScript, and the free `wttr.in` weather API (no key required). A `pytest` suite
covers tools, security, agents, memory, and the MCP server; `eval/run_eval.py`
runs rubric‑style checks.

## Run it

The repository includes a one‑page `QUICKSTART.md`. In short: create a Python
venv and `pip install -r requirements.txt`, copy `.env.example` to `.env` and add
your `GOOGLE_API_KEY`, start the backend with `uvicorn backend.main:app --port
8000`, then `cd frontend && npm install && npm run dev` and open
`http://localhost:5173`. A live deploy isn't required to run it — the public repo
with these instructions is the project link.

**Repository:** https://github.com/gundujeevesh123/weekpilot

## Limitations and future work

WeekPilot uses in‑memory sessions (a production build would persist to a database),
weather is limited to a 3‑day public forecast, and there's no calendar/email API
integration yet. Natural next steps: a hard‑constraint scheduler (Google OR‑Tools)
for guaranteed clash‑free time‑blocking, Google Calendar sync, consented email
sending, and a Cloud Run + Firebase deployment for a public URL.

---

*Built for the Google × Kaggle AI Agents Intensive (Vibe Coding) Capstone —
Concierge Agents track. Licensed under CC‑BY 4.0.*
