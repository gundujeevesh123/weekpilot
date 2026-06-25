# WeekPilot — 5‑Minute YouTube Video Script

A friendly, flowing script for your capstone demo video. Target length **≈ 5:00**
(stay under the 5‑minute limit). Narration is written to be spoken naturally —
read it like you're showing a friend. **Square brackets = stage directions**
(what to show / where to be / what to click).

### Before you hit record
- Have **two things open and ready**: (1) your `README.md` scrolled to the top,
  and (2) the running web app at **http://localhost:5173** (backend + `npm run dev`
  already started, browser clean with no extra tabs).
- Record at 1080p with a clear mic. A calm, friendly tone beats fast and salesy.
- You can be on camera for the intro/outro, or do voiceover the whole way — both
  are fine.

---

## 0:00 – 0:20 · Hook
[On camera, or voiceover over the WeekPilot app home screen with the rocket logo.]

> "Hi! I'm [your name], and this is **WeekPilot** — an AI agent that plans your
> whole week from a single sentence, while keeping your personal data private.
> Let me show you why I built it, and how it works."

---

## 0:20 – 0:50 · The problem
[Screen‑share. Keep your **README open** and slowly scroll to the "The Problem"
section as you talk — having it on screen shows the judges your documentation.]

> "Every week we juggle tasks, messages, meetings, and even the weather — across
> half a dozen different apps. And most AI assistants quietly collect your
> personal data to help. I wanted the opposite: one friendly assistant that
> handles the entire week, and never remembers anything personal without asking
> first. That's WeekPilot — built for the **Concierge Agents** track."

---

## 0:50 – 1:20 · Why an agent (not just a chatbot)
[Stay on the README; scroll toward the architecture diagram as you finish.]

> "So why an *agent*, and not just a chatbot? Because planning a week isn't one
> task — it's many. 'Help me get ready for Monday' could mean creating tasks,
> drafting an email, or checking the weather. A single prompt can't juggle all
> that. So WeekPilot works like a small team: one coordinator reads what you
> want, and hands each job to the right specialist."

---

## 1:20 – 2:10 · Architecture (point as you explain)
[Screen‑share the **architecture diagram in the README**. Point at each piece
with your cursor as you name it — this keeps it easy to follow.]

> "Here's that team. [point to orchestrator] The **orchestrator** routes your
> request. [point] **Task Triage** organizes and prioritizes your to‑dos.
> [point] The **Schedule Planner** blocks out your week and checks the weather.
> [point] The **Message Drafter** writes emails — but only sends them after you
> approve. And **research** runs as a tool, using Google Search.
>
> [point to the MCP server box] Now here's the part I'm proud of: the weather
> and date tools live in their own **MCP server** — a separate little service
> that *only ever sees public data*, like a city name. Your tasks, messages, and
> personal details never cross that line. The privacy promise is built right
> into the architecture."

---

## 2:10 – 3:40 · Live demo (the heart of the video)
[Switch to the **running web app at localhost:5173**. Have it open already so
there's no waiting.]

> "Okay — let's actually use it."

[Click the input box and type this prompt, then press Enter:]
> *"Plan my week in London: gym Mon/Wed/Fri 7am, deep‑work mornings, dinner with
> Sam Friday — check the weather."*

[Point at the animated typing dots while it thinks, then let the answer render.
Scroll slowly through the weekly plan.]

> "And there's my whole week — time‑blocked day by day: gym sessions, deep‑work
> mornings, dinner with Sam, and a weather note pulled live through that MCP
> server. One sentence in, a full plan out."

[Now the privacy moment. Type a message that contains personal info:]
> *"By the way, my doctor's email is doc@clinic.com."*

[Send it, and point at the consent prompt that appears.]

> "And here's the privacy promise in action. WeekPilot noticed the email address
> and is *asking* before it remembers it. I'll say no — [type "no"] — and it
> forgets. Your data, your choice. Nothing personal is stored unless you say so."

---

## 3:40 – 4:30 · How it's built + security
[Optional: briefly show your code editor or the README's security section, then
come back to the app. Speak warmly — this is the technical payoff.]

> "Under the hood, WeekPilot runs on **Google's Agent Development Kit** with
> **Gemini**, a **FastAPI** backend, and a **React** front‑end. The API key
> stays on the server — it's never exposed to your browser.
>
> Security isn't bolted on at the end — it's built in. Every input is checked,
> prompt‑injection attempts are blocked, personal data is scrubbed from the
> logs, and only approved tools are allowed to run — each one backed by a test
> that proves it works. And if Gemini ever gets busy, the app quietly retries
> instead of throwing an error at you."

---

## 4:30 – 5:00 · Wrap‑up
[Back on camera, or on the app's home screen.]

> "So that's WeekPilot: a multi‑agent system, a Model Context Protocol server,
> and privacy‑first security — a friendly concierge that plans your week without
> ever compromising your data. All the code and setup steps are on GitHub, in
> the link below. Thanks so much for watching!"

[End card on screen for 3–4 seconds:]
> **github.com/gundujeevesh123/weekpilot**
> *Built for the Google × Kaggle AI Agents Intensive — Concierge Agents track*

---

### Quick timing cheat‑sheet
| Section | Time | What's on screen |
|---|---|---|
| Hook | 0:00–0:20 | You / app home |
| Problem | 0:20–0:50 | README (problem) |
| Why an agent | 0:50–1:20 | README → diagram |
| Architecture | 1:20–2:10 | README diagram (point) |
| Demo | 2:10–3:40 | Web app at :5173 |
| Build + security | 3:40–4:30 | Code / README / app |
| Wrap | 4:30–5:00 | You / end card |

Tip: if you run long, trim the build‑and‑security section first — the demo and
the privacy moment are what win the Pitch points.
