# WeekPilot Web App — Run & Deploy Guide

A beautiful React UI (in `frontend/`) talking to a thin, secure FastAPI backend
(in `backend/`) that wraps the existing WeekPilot ADK agent. The earlier `503`
you saw was Gemini being overloaded — every agent now retries transient
`429/5xx` errors automatically (`weekpilot/model_config.py`).

```
Browser (React)  ──/api/chat──►  FastAPI backend  ──►  WeekPilot ADK agent  ──►  Gemini
  frontend/ :5173                 backend/ :8000        (your existing code)      (key stays server-side)
```

---

## 1. One-time setup

**Backend (Python 3.10+):**
```bash
cd kaggle-google-project
python -m venv .venv
.venv\Scripts\activate                 # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env                 # Windows  (cp on macOS/Linux); add your GOOGLE_API_KEY
```

**Frontend (Node 18+):**
```bash
cd frontend
# If a partial "node_modules" folder exists from earlier, delete it first.
npm install
```

---

## 2. Run it (two terminals)

**Terminal 1 — backend:**
```bash
cd kaggle-google-project
.venv\Scripts\activate
uvicorn backend.main:app --port 8000
```

**Terminal 2 — frontend:**
```bash
cd kaggle-google-project\frontend
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api` to the backend
on :8000, so there are no CORS issues in development.

To preview the production build: `npm run build` then `npm run preview`.

---

## 3. How to use it

Type plain language; the orchestrator routes to the right specialist. Try the
suggestion chips, or:
- "Plan my week in London: gym Mon/Wed/Fri 7am, deep-work mornings, dinner with Sam Friday — check the weather."
- "Add tasks: finish Q3 proposal by Thursday (high priority), book dentist, reply to Sam — then prioritize them."
- "Draft a friendly email to my manager asking for Friday off."

UI niceties: light/dark toggle, "New chat" to reset the session, animated typing
indicator, and a one-click **Try again** on any error (handy if Gemini is busy).

---

## 4. Security & privacy design (your data stays protected)

- **API key never reaches the browser.** It's read server-side from `.env`; the
  frontend only ever sends your message text.
- **CORS is locked** to explicit origins (`WEEKPILOT_CORS_ORIGINS`), never `*`.
- **Input is length-limited** (2,000 chars) and the agent's existing guardrails +
  PII-redaction callbacks run on every turn.
- **No internal leakage:** only the final assistant text + an opaque session id
  are returned — no stack traces, traces, or tool internals.
- **Minimal data retention:** sessions are in-memory, keyed by a random UUID; no
  personal data is written to disk by the web layer.
- **MCP boundary unchanged:** weather/date tools still run over local stdio with
  no PII (see `COMPETITION_COMPLIANCE_AND_LAUNCH.md`).
- **Secrets stay out of git:** `.env` and `frontend/node_modules` are git-ignored.

---

## 5. Deploying (optional) — the realistic Google path

Note: **Google AI Studio cannot host a full web app** (it's for prototyping
prompts/models). For a public URL, use Google Cloud — both have generous free
tiers and scale to zero (so cost stays ~$0 at low traffic):

1. **Backend → Cloud Run.** Containerize `backend/` (uvicorn), set `GOOGLE_API_KEY`
   via **Secret Manager** (not a committed file), and set `WEEKPILOT_CORS_ORIGINS`
   to your frontend's URL. Cloud Run gives an HTTPS endpoint and scales to zero.
2. **Frontend → Firebase Hosting** (or Cloud Run static). Build with
   `npm run build` and point the app at the Cloud Run backend URL.

For the Kaggle submission you do **not** need to deploy — a public GitHub repo
with these instructions satisfies the "public project link" requirement. If you
do deploy, add the reproduction steps to your writeup.

---

## 6. Notes

- The backend uses ADK's in-memory sessions (lightweight). For persistence across
  restarts, switch to `DatabaseSessionService` (SQLite/Cloud SQL) later.
- If you ever expose the backend publicly without the React app, keep CORS locked
  and consider adding auth + rate limiting before going public.
