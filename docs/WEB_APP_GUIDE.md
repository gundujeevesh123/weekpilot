# WeekPilot Web App — Run & Deploy Guide

A beautiful React UI (in `frontend/`) talking to a thin, secure FastAPI backend
(in `backend/`) that wraps the existing WeekPilot ADK agent. The earlier `503`
you saw was Gemini being overloaded — every agent now retries transient
`429/5xx` errors automatically (`weekpilot/model_config.py`).

```
Browser (React)  ──/api/chat──►  FastAPI backend  ──►  WeekPilot ADK agent  ──►  Gemini
  frontend/ :5173                 backend/ :8000        (your existing code)      (key stays server-side)
```

## What's new in the UI

- **Split dashboard + chat.** A live **My Week** panel sits beside the chat. Ask
  WeekPilot to "plan my week…" and the schedule fills in automatically.
- **Tabular schedule.** Schedules render as a clean **Day · Time · Work · Notes**
  table (the agent now emits a Markdown table the dashboard parses).
- **Weather chips + workload bars.** Each day shows its weather and a load bar;
  days over ~8h get an overload warning (inspired by Sunsama/Reclaim, but inline).
- **Bright blue/white theme** with light & dark modes, a privacy-first badge, a
  no-blank-page sample week, and mobile tabs (My Week / Chat).
- **Single public URL.** In production the backend serves the built UI, so the
  whole app lives behind one HTTPS address you can share with anyone.

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

## 5. Share it with others — free public URL (recommended path)

The app is packaged as a **single Docker image** that builds the React UI and
serves it from FastAPI, so one HTTPS URL serves both the app and the `/api`.
Anyone you give that URL to can use WeekPilot — no install, no localhost.

### Option A — Render (free, ~5 minutes, no credit card)

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New → Blueprint** → pick your repo.
   Render reads `render.yaml` and configures everything.
3. When prompted, paste your Google AI Studio key into **`GOOGLE_API_KEY`**
   (get one at <https://aistudio.google.com/apikey>). It's stored as a secret and
   is **never** sent to the browser.
4. **Create** → you get a URL like `https://weekpilot.onrender.com`. Share it. ✅

   *Free plan note:* the service sleeps after ~15 min idle; the first visit after
   that cold-starts in ~30s, then it's snappy. Cost stays $0 at low traffic.

### Option B — any Docker host (Railway, Fly.io, Cloud Run, a VPS)

```bash
docker build -t weekpilot .
docker run -p 8000:8000 -e GOOGLE_API_KEY=your-key weekpilot
# open http://localhost:8000  (or the host's public URL)
```

On Railway/Fly/Cloud Run: deploy the `Dockerfile`, set `GOOGLE_API_KEY` as a
secret, and the platform's injected `$PORT` is used automatically.

### Run the production build locally (no Docker)

```bash
cd frontend && npm run build && cd ..
uvicorn backend.main:app --host 0.0.0.0 --port 8000
# Now http://<your-LAN-ip>:8000 works for others on your Wi-Fi too.
```

For the Kaggle submission you do **not** need to deploy — a public GitHub repo
satisfies the "public project link" requirement. If you do deploy, add the URL
and these steps to your writeup.

---

## 6. Notes

- The backend uses ADK's in-memory sessions (lightweight). For persistence across
  restarts, switch to `DatabaseSessionService` (SQLite/Cloud SQL) later.
- If you ever expose the backend publicly without the React app, keep CORS locked
  and consider adding auth + rate limiting before going public.
