# Why I Built WeekPilot

I built WeekPilot because I was tired of AI assistants that treat my personal
data like it's theirs.

Every week, I juggle tasks, messages, meetings, and research across multiple
apps. I wanted a single AI concierge that could handle it all — but with one
non-negotiable rule: **my data stays mine unless I explicitly say otherwise.**

Most AI productivity tools auto-collect everything. WeekPilot flips that model.
It uses a consent-gated memory system that detects sensitive information
(emails, phone numbers, personal details) and asks for permission before
remembering anything. If you say no, it forgets.

The multi-agent architecture isn't complexity for its own sake. Each planning
domain (tasks, messages, schedules, research) requires different reasoning,
different tools, and different rules. The orchestrator + specialist pattern
keeps each agent focused and testable, while the shared security layer
ensures every interaction is validated, logged, and privacy-respecting.

WeekPilot proves that AI agents can be both genuinely useful and genuinely
private — and that's a combination worth building.
