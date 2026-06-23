# WeekPilot Demo Video Script — 3-Minute Explainer

> **Total runtime:** ~3 minutes | **Format:** Screen recording + voiceover
> **Resolution:** 1080p | **Style:** Clean, professional, energetic

---

## Beat 1: Hook (0:00–0:10)

**🎬 ON SCREEN:** WeekPilot logo/title card with tagline:
*"Plan your week. Keep your privacy."*

**🎙️ VOICEOVER:**
> "What if your AI assistant planned your entire week — tasks, messages,
> schedule — but NEVER stored your personal data without asking first?"

---

## Beat 2: The Problem (0:10–0:30)

**🎬 ON SCREEN:** Quick montage of multiple app icons (calendar, email, to-do,
weather) — then transition to a single WeekPilot interface.

**🎙️ VOICEOVER:**
> "Professionals juggle tasks across a dozen apps. Most AI assistants
> quietly collect your data. WeekPilot changes that — it's a single
> concierge that handles your whole week, with privacy built in from
> the ground up."

---

## Beat 3: Live Demo — Task Management (0:30–1:00)

**🎬 ON SCREEN:** ADK web UI. Type: *"I need to prepare a quarterly
presentation by Friday, buy groceries, and schedule a dentist appointment."*

**🎙️ VOICEOVER:**
> "Watch: I give WeekPilot three tasks. The orchestrator routes to the
> Task Triage agent, which creates each one and auto-classifies by
> urgency using the Eisenhower matrix."

**🎬 SHOW:** Agent response with color-coded priority tasks.
**🎬 SHOW:** Type *"Prioritize my tasks"* — see Eisenhower-sorted list.

---

## Beat 4: Live Demo — Message Drafting (1:00–1:30)

**🎬 ON SCREEN:** Type: *"Draft an email to my manager about taking Friday
off for the dentist."*

**🎙️ VOICEOVER:**
> "The orchestrator routes this to the Message Drafter — which composes
> a professional email and presents it for my approval. It never auto-sends.
> That's human-in-the-loop in action."

**🎬 SHOW:** Draft message with "approve" prompt.
**🎬 SHOW:** Type *"Looks good, approve it"* — draft marked approved.

---

## Beat 5: Live Demo — Schedule + Weather (1:30–2:00)

**🎬 ON SCREEN:** Type: *"Plan my week. I'm in San Francisco and want to
jog outdoors on Wednesday."*

**🎙️ VOICEOVER:**
> "The Schedule Planner checks the weather via a REST API, sees rain on
> Wednesday, and suggests moving the jog to Thursday. Smart scheduling
> that accounts for real-world conditions."

**🎬 SHOW:** Weather forecast + rescheduled weekly plan.

---

## Beat 6: Architecture & Security (2:00–2:30)

**🎬 ON SCREEN:** Architecture diagram (from README) — highlight the 4
specialist agents, the security layer, and the consent-gated memory.

**🎙️ VOICEOVER:**
> "Under the hood: an orchestrator routes to four specialist agents,
> each with focused tools and least-privilege access. Security is
> shifted left — STRIDE threat model, input sanitization, PII
> redaction, and tool allow-listing are all implemented as code,
> not bolted on afterward."

**🎬 ON SCREEN:** Quick flash of test results — all passing.

**🎙️ VOICEOVER:**
> "Every guardrail has a test proving it works. Prompt injection?
> Blocked. PII in logs? Redacted. Unauthorized tools? Denied."

---

## Beat 7: Privacy Moment (2:30–2:45)

**🎬 ON SCREEN:** Type: *"Remember that my doctor's email is doc@clinic.com"*

**🎙️ VOICEOVER:**
> "Here's the privacy promise in action. WeekPilot detects the email
> address and asks: 'May I save this to long-term memory?' If I say
> no — it forgets. Your data, your choice."

**🎬 SHOW:** Consent prompt → type "no" → agent confirms data discarded.

---

## Beat 8: Impact & Close (2:45–3:00)

**🎬 ON SCREEN:** Summary card:
- ✅ 4 specialist agents
- ✅ 14 tools (custom + search + REST API)
- ✅ Consent-gated memory
- ✅ Full STRIDE security
- ✅ All 5 course concepts

**🎙️ VOICEOVER:**
> "WeekPilot proves that AI assistants can be both powerful AND
> privacy-respecting. Built with Google ADK 2.0 and Gemini 2.5 Flash.
> Plan your week. Keep your privacy. Thanks for watching."

**🎬 ON SCREEN:** GitHub link + "Built for Google × Kaggle AI Agents Intensive"

---

## Production Notes

| Item | Detail |
|------|--------|
| **Recording tool** | OBS Studio or Loom |
| **Screen** | ADK web UI at localhost (clean browser, no tabs) |
| **Audio** | Clear voiceover, no background music needed |
| **Transitions** | Simple fade between beats |
| **Duration check** | Each beat timed — total ≤ 3:00 (under the 5:00 limit) |
