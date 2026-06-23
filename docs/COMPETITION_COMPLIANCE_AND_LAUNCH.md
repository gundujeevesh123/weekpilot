# WeekPilot — Competition Compliance & Launch Guide

Checked against the **AI Agents: Intensive Vibe Coding Capstone Project**
(Kaggle, sponsored by Google). Reviewed: Overview, Submission Requirements,
Tracks, Evaluation, Rules. Last updated 2026-06-23.

**Recommended track:** **Concierge Agents** — WeekPilot is a privacy-first
personal concierge that keeps personal data local and consent-gated, which is
exactly what this track rewards ("keeps personal information safe and secure").

**Deadline:** Submissions due **July 6, 2026, 11:59 PM PT** (= Jul 7, 2026,
12:29 PM IST). Each team may submit **one** writeup only.

---

## 1. Compliance checklist (code / repo requirements)

| Requirement (from Rules / Evaluation) | Status | Notes |
|---|---|---|
| **Winner License = CC-BY 4.0** | ✅ Pass | `LICENSE` is CC BY 4.0; `pyproject.toml` declares `CC-BY-4.0`. Matches the required license exactly. |
| **🚨 No API keys or passwords in code** | ✅ Pass (with one action) | `.env` is git-ignored; no git repo exists yet, so the key has never been committed. The only `AIza…` string in the code is a **fake example** inside a docstring in `security/guardrails.py`. **Action:** before publishing, rotate the key as a precaution, and commit `.gitignore` *before* `git add .`. |
| **Apply ≥ 3 course concepts** | ✅ Pass (3 in code) | In **code**: (1) Multi-agent system / ADK — orchestrator + 4 specialists; (2) Security features — callbacks, PII redaction, guardrails, consent; (3) **MCP Server** — `weekpilot/mcp_server/` exposes public-data tools (weather, date/time) over stdio, consumed via ADK `McpToolset`. The video can further show Deployability + ADK CLI. Comfortably exceeds the minimum of 3. |
| **README with problem, solution, architecture, setup, diagrams** | ✅ Pass | `README.md` covers all of these with an architecture diagram. Setup now works (see fix below). |
| **Code comments on implementation/design/behavior** | ✅ Pass | Google-style docstrings throughout; `CONTEXT.md` documents standards. |
| **Public project link OR public repo + detailed setup** | ⚠️ To do | No live deploy required. You need a **public GitHub repo** with these setup steps. Repo not created yet (no `.git`). See §3. |
| **Reasonably-accessible, low-cost tools/models** | ✅ Pass | Gemini (free tier) + free `wttr.in` weather API. Explicitly allowed by Rule 2.6. |
| Single submission / team ≤ 5 / one Kaggle account | ✅ N/A in code | Process rules — just don't submit from multiple accounts. |

### The agent must actually run (for the demo + 50-pt implementation score)
A separate bug was fixed earlier this session: the ADK tool-callback signatures
in `weekpilot/security/callbacks.py` didn't match ADK 2.3.0, which crashed
schedule planning with a `TypeError`. That is now fixed and tested, so the
weather/reminder/task tools work — essential for your demo video.

---

## 2. Changes made for compliance (only inside this folder)

1. **Added `.env.example`** — the README told users to `copy .env.example .env`,
   but the file didn't exist, breaking setup instructions (hurts the 20-pt
   Documentation score). The template carries placeholders only — no real key.
2. **Made the README setup OS-aware** (`copy` on Windows, `cp` on macOS/Linux)
   and reinforced "never commit `.env`."
3. (Earlier) **Fixed the tool-callback signature bug** so the agent runs.

Nothing else needed changing for rule compliance — license, secret handling,
multi-agent design, and documentation already meet the requirements.

---

## 3. Publish the public repo (required submission asset)

Run these from the project folder. The order matters — commit `.gitignore`
first so `.env` can never be staged:

```bash
git init
git add .gitignore            # ensures secrets are excluded first
git commit -m "Add gitignore"
git add .                     # .env, *.db, *.log, .venv are auto-excluded
git status                    # CONFIRM .env is NOT listed
git commit -m "WeekPilot — privacy-first weekly concierge agent"
# Create an empty PUBLIC repo on github.com, then:
git remote add origin https://github.com/<you>/weekpilot.git
git push -u origin main
```

Then put that GitHub URL in your Kaggle Writeup as the "Public Project Link."

---

## 4. MCP Server (built — 3rd in-code concept)

`weekpilot/mcp_server/` is a Model Context Protocol server that exposes two
**public-data** tools — `get_weather_forecast` and `get_current_datetime` — which
the schedule planner consumes through ADK's `McpToolset`
(`weekpilot/agents/schedule_planner.py`). Layout:

- `tools_impl.py` — transport-independent logic (stdlib + lazy `requests`); no MCP
  or WeekPilot-package imports, so it is isolated and unit-tested offline.
- `server.py` — thin FastMCP wrapper that registers the two tools and runs over
  **stdio**.

**Security design (confidentiality, integrity, availability):**
- **Stdio transport** — launched as a local child process; no network port is
  opened, so there is no remote attack surface.
- **No PII crosses the boundary** — the server only ever sees public data (city
  names, timezones). Tasks, reminders, messages, and all personal data stay in
  the agent's in-process session state.
- **No secrets** — the weather source (wttr.in) needs no API key.
- **Defense in depth** — inputs are sanitised and clamped; the external response
  is treated as untrusted (allow-listed fields only); `tool_filter` enforces
  least privilege; and the agent's before/after-tool security callbacks still
  govern every MCP call (the new tool is on the guardrails allow-list).

**Verify it:**

```bash
pytest tests/test_mcp_server.py -v          # offline logic + sanitisation tests
python -m weekpilot.mcp_server.server       # boots the stdio server (Ctrl-C to stop)
```

(The server boot + tool registration was verified against the MCP SDK during the
build; both tools register with generated input schemas.)

---

## 5. How to launch the agent

**Prerequisites:** Python 3.10+, a Google AI Studio API key.

```bash
cd kaggle-google-project
python -m venv .venv
.venv\Scripts\activate            # Windows  (use: source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env            # Windows  (cp on macOS/Linux); then paste your GOOGLE_API_KEY
```

**Run it (pick one):**

```bash
adk web weekpilot/                # Browser chat UI at http://localhost:8000  — best for the demo video
adk run weekpilot/                # Terminal chat
pytest tests/ -v                  # Run the test suite
python eval/run_eval.py           # Structural evaluation (no API key needed)
```

For the video, `adk web` is ideal: it shows the orchestrator routing to
sub-agents and the tool calls live.

---

## 6. How to give inputs

Talk to WeekPilot in **plain natural language** — the orchestrator decides which
specialist handles each request. Good demo prompts, by capability:

- **Tasks (triage):** "Add three tasks: finish the Q3 proposal by Thursday (high
  priority), book a dentist appointment, and reply to Sam. Prioritize them."
- **Schedule the week** (this is the one that used to crash): "Plan my week in
  London. I want gym Mon/Wed/Fri at 7am, deep-work mornings, team standup daily
  at 10am, and dinner with Sam on Friday. Check the weather for outdoor runs."
- **Reminders:** "Remind me to submit the report on 2026-06-30 at 09:00."
- **Messages (draft + approve):** "Draft a friendly email to my manager asking
  for Friday off." → review → "Approve it."
- **Research:** "Find a good vegetarian restaurant near downtown London for
  Friday's dinner."
- **Privacy/consent demo:** include a personal detail ("my email is
  me@example.com") and show WeekPilot asking for consent before remembering it —
  a perfect fit for the Concierge track.

Tips: give one clear request at a time for a clean demo; include a **city** when
you want weather-aware scheduling; use dates as `YYYY-MM-DD` and times as
`HH:MM` for reminders.

---

## 7. Submission checklist (do on Kaggle before the deadline)

- [ ] Code fixes pulled in and agent runs (`adk web weekpilot/`).
- [ ] Public GitHub repo pushed (`.env` excluded) — §3.
- [ ] Record a demo video **≤ 5 minutes**, upload to **YouTube** (public/unlisted).
- [ ] Create a **Kaggle Writeup** (≤ 2,500 words): title, subtitle, problem,
      solution, architecture, build story. Attach a **cover image** + the video.
- [ ] Add the **public project link** (your GitHub URL).
- [ ] **Select the track: Concierge Agents.**
- [ ] Click **Submit** (a saved draft is NOT a submission).
