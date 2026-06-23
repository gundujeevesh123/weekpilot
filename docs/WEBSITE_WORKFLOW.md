# WeekPilot → Website: Architecture, Model Stack & Build Workflow

*Companion to the WeekPilot ADK agent. Covers (1) the bug that caused the "file
errors" during schedule planning and how it was fixed, and (2) the end-to-end
workflow to turn this agent into a website where a user types their plans and
gets a full week scheduled.*

Last updated: 2026-06-23

---

## 1. What was broken (and the fix)

### Symptom
The agent greeted you fine, but the moment you asked it to **plan a schedule** it
threw "a bunch of file errors." Those errors were a multi-line Python
**traceback** (every `File "...", line N` line is one frame of the stack), not a
problem with reading/writing files.

### Root cause — tool-callback signature mismatch
`weekpilot/security/callbacks.py` declared the tool callbacks as:

```python
def before_tool_security_callback(callback_context, tool_name, tool_args): ...
def after_tool_security_callback(callback_context, tool_name, tool_result): ...
```

But Google ADK **2.3.0** invokes them with *keyword* arguments:

```python
before_tool_callback(tool=<BaseTool>, args=<dict>, tool_context=<ToolContext>)
after_tool_callback (tool=<BaseTool>, args=<dict>, tool_context=<ToolContext>, tool_response=<dict>)
```

Because the parameter names don't match, Python raises
`TypeError: got an unexpected keyword argument 'tool'` **the instant any tool
runs**. The greeting worked because it only fires the *model* callbacks
(`before_model` / `after_model`), whose signatures were already correct.
Scheduling was simply the first thing you tried that needs a tool
(`get_weather_forecast`, `set_reminder`) — so it was the first thing to crash.

This was verified directly against the ADK 2.3.0 source
(`google/adk/flows/llm_flows/functions.py`).

### The fix (applied)
- `before_tool_security_callback(tool, args, tool_context)` and
  `after_tool_security_callback(tool, args, tool_context, tool_response)` now
  match ADK's contract. The security logic is unchanged — the tool name is read
  from `tool.name`, and PII scrubbing still mutates the response in place.
- `tests/test_security.py` was updated to call the callbacks the way ADK does
  (a `SimpleNamespace(name=...)` tool stub), plus a new regression test for the
  `after_tool` signature so this can't silently break again.

### One more issue to expect next — `google_search` in a sub-agent
`research_agent` uses the built-in `google_search` tool **and** is registered as
a `sub_agent`. ADK has a known limitation here: when the orchestrator delegates
via function-calling and the sub-agent then uses a built-in tool, the Gemini API
can return `400 INVALID_ARGUMENT: Tool use with function calling is
unsupported`. ADK ≥1.16 ships a partial workaround, but multi-agent execution
can still fail (see adk-python issue #4449).

**Recommended fix:** convert `research_agent` from a `sub_agent` into an
**Agent-as-Tool**:

```python
from google.adk.tools.agent_tool import AgentTool
# in agent.py, drop research_agent from sub_agents and instead expose it as a tool:
tools=[AgentTool(agent=research_agent)]
```

This keeps research isolated and sidesteps the built-in-tool delegation limit.

---

## 2. Recommended model stack (June 2026)

This is a Google × Kaggle capstone, so the backend stays on **Gemini**. Map
models to roles by cost/latency, not one model for everything.

| Role in WeekPilot | Recommended model | Why |
|---|---|---|
| Orchestrator routing, Task Triage, Message Drafter, **Schedule Planner** | **Gemini 2.5 Flash** (dev / free tier) → **Gemini 3.5 Flash** (production) | 3.5 Flash (released May 2026) beats 3.1 Pro on agentic + coding benchmarks, ~4× faster, and is cheaper than Pro. 2.5 Flash keeps the free tier for development. |
| Research grounding | Same Flash model + **Google Search grounding** | Built-in grounding tool; no separate model needed. |
| Hard scheduling constraints (no overlaps, work hours, buffers) | **Google OR-Tools (CP-SAT)** — *not* an LLM | Deterministic constraint solving is more reliable than asking an LLM to avoid clashes. The LLM extracts tasks + constraints; OR-Tools places the blocks; the LLM explains the result. |
| Optional fallback for very complex weeks / long context | **Gemini 3.1 Pro** (2M context) | Use only when a request is large or highly constrained; more expensive. |

Indicative API pricing (per 1M tokens, mid-2026): Gemini 3.5 Flash ~$1.50 in /
$9.00 out; 3.1 Flash-Lite ~$0.25 / $1.50; 3.1 Pro ~$4.00 / $18.00; 2.5 Flash has
a restricted free tier. Confirm live pricing before launch — see Sources.

**Config change to make this easy:** the orchestrator already reads
`WEEKPILOT_MODEL` from the environment, but the four sub-agents hardcode
`"gemini-2.5-flash"`. Have them read the same env var (default `gemini-2.5-flash`)
so you can switch the whole app to `gemini-3.5-flash` with one setting.

---

## 3. Target architecture (the website)

```
┌──────────────┐   HTTPS/JSON   ┌───────────────────────┐   Gemini API   ┌────────────┐
│  Frontend    │ ─────────────▶ │  Backend (FastAPI)    │ ─────────────▶ │  Gemini    │
│  React/Vite  │                │  ADK Runner +         │                │  3.5 Flash │
│  + Tailwind  │ ◀───────────── │  weekpilot root_agent │ ◀───────────── │            │
└──────────────┘   WeekPlan     └───────────┬───────────┘                └────────────┘
      ▲           (structured)              │
      │                                     ├── OR-Tools CP-SAT  (time-block solver)
      │                                     ├── wttr.in           (weather)
      │                                     └── Session store     (SQLite → Cloud SQL)
      └── renders day-by-day weekly grid
```

### Backend
- **Keep the ADK agent as the engine.** Expose it over HTTP one of two ways:
  - Fast path: `adk api_server weekpilot/` — starts a Uvicorn + FastAPI server
    with REST endpoints and `--allow_origins` for CORS.
  - Custom path: your own FastAPI app that creates a session and calls
    `Runner.run_async(...)`, so you can add `/plan-week`, auth, and rate limits.
- **Return structured output, not prose.** You already have the `WeekPlan`
  Pydantic schema (`weekpilot/models/schemas.py`). Have `schedule_planner_agent`
  emit a `WeekPlan` (via an `output_schema` or a `save_week_plan` tool) so the
  frontend renders a real grid instead of parsing markdown.
- **Sessions:** `DatabaseSessionService` — SQLite locally (already present at
  `weekpilot/.adk/session.db`), Postgres/Cloud SQL in production.
- **Deploy:** containerize and ship to **Google Cloud Run** (autoscaling,
  no infra to manage). Load `GOOGLE_API_KEY` from Secret Manager, not `.env`.

### Frontend
- **Stack:** React + Vite + TypeScript + Tailwind, with **shadcn/ui** components
  and **TanStack Query** for the API calls. (Next.js is a fine alternative if you
  want SSR + API routes in one project.)
- **Core screen:** a single "Plan my week" input (free-text box: *"Gym Mon/Wed/Fri
  7am, finish proposal by Thursday, dinner with Sam Friday…"*) → POST to backend →
  render the returned `WeekPlan` as a 7-day column grid with time blocks, plus a
  chat panel to refine ("move the gym to evenings").
- **Deploy:** Vercel or Firebase Hosting; point it at the Cloud Run backend URL.

### Request flow
1. User types plans → React `POST /plan-week { text }`.
2. FastAPI gets/creates an ADK session, runs `root_agent`.
3. Orchestrator routes to `schedule_planner_agent`; it pulls tasks from state,
   checks weather, (optionally) calls OR-Tools to place non-overlapping blocks.
4. Agent returns a `WeekPlan` JSON; FastAPI streams events / returns final JSON.
5. React renders the weekly grid; follow-up messages reuse the session id.

---

## 4. Suggested build order

1. **Done:** fix tool-callback signatures so tools (and scheduling) work.
2. Convert `research_agent` to an Agent-as-Tool (section 1) and re-test research.
3. Make sub-agents read `WEEKPILOT_MODEL`; set it to `gemini-3.5-flash` for prod.
4. Add structured `WeekPlan` output to `schedule_planner_agent`.
5. (Optional but recommended) add an OR-Tools solver tool for clash-free blocks.
6. Stand up the backend: `adk api_server` or a thin FastAPI wrapper; enable CORS.
7. Build the React form + weekly-grid UI against the API.
8. Containerize → Cloud Run (backend) + Vercel/Firebase (frontend); secrets in
   Secret Manager.
9. Keep `pytest` + `eval/run_eval.py` green in CI before each deploy.

---

## Sources
- ADK tool limitations — https://google.github.io/adk-docs/tools/limitations/
- adk-python issue #4449 (sub-agent + GoogleSearch fails) — https://github.com/google/adk-python/issues/4449
- ADK Cloud Run deploy — https://google.github.io/adk-docs/deploy/cloud-run/
- ADK API server — https://google.github.io/adk-docs/runtime/api-server/
- Adding a REST API to an ADK app with FastAPI — https://medium.com/google-cloud/get-schwifty-with-the-fastapi-adding-a-rest-api-to-our-agentic-application-with-google-adk-6b87a4ea7567
- Gemini API pricing — https://ai.google.dev/gemini-api/docs/pricing
- Gemini 2026 pricing overview — https://www.opslyft.com/blog/google-gemini-api-pricing-2026
