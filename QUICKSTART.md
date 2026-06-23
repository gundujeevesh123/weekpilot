# WeekPilot — Quickstart

Run the full app (beautiful React UI + secure FastAPI backend + your ADK agent).
Commands are Windows-first; macOS/Linux alternates noted.

## Prerequisites
- Python 3.10+  ·  Node 18+  ·  a Google AI Studio API key (https://aistudio.google.com/apikey)

## 1) Backend — one-time setup
```bat
cd C:\Users\bharadwaj\Downloads\kaggle-google-project
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
```
In `.env`, set `GOOGLE_API_KEY=your-key-here`, then save and close.
(macOS/Linux: `source .venv/bin/activate`, `cp .env.example .env`.)

## 2) Frontend — one-time setup
```bat
cd C:\Users\bharadwaj\Downloads\kaggle-google-project\frontend
rmdir /s /q node_modules
npm install
```
(The `rmdir` clears a leftover partial folder; ignore "not found". macOS/Linux: `rm -rf node_modules`.)

## 3) Run it — two terminals

Terminal A — backend:
```bat
cd C:\Users\bharadwaj\Downloads\kaggle-google-project
.venv\Scripts\activate
uvicorn backend.main:app --port 8000
```

Terminal B — frontend:
```bat
cd C:\Users\bharadwaj\Downloads\kaggle-google-project\frontend
npm run dev
```

Open **http://localhost:5173** and start typing, e.g.
*"Plan my week in London: gym Mon/Wed/Fri 7am, deep-work mornings, dinner with Sam Friday — check the weather."*

---

## Optional / handy
- Run the test suite:           `pytest tests/ -v`
- Check the MCP server boots:    `python -m weekpilot.mcp_server.server`  (Ctrl-C to stop)
- Old ADK developer UI:          `adk web weekpilot/`
- If Gemini returns 503 a lot, switch to a lighter model in Terminal A **before** uvicorn:
  - Windows:      `set WEEKPILOT_MODEL=gemini-2.5-flash-lite`
  - macOS/Linux:  `export WEEKPILOT_MODEL=gemini-2.5-flash-lite`
  (Retries are already automatic; this just uses a less-busy model.)

## If something fails
- `ModuleNotFoundError` → make sure the venv is active and `pip install -r requirements.txt` finished.
- Frontend build/type errors → delete `frontend/node_modules` and re-run `npm install`.
- Port already in use → change `--port 8000` (and update `frontend/vite.config.ts` proxy to match).
