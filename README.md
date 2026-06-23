# 🚀 WeekPilot — Privacy-First Weekly Concierge Agent

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Built with ADK](https://img.shields.io/badge/Built%20with-Google%20ADK%202.0-4285F4.svg)]()
[![Powered by Gemini](https://img.shields.io/badge/Powered%20by-Gemini%202.5%20Flash-FF6F00.svg)]()

> **A privacy-first personal concierge agent that plans your week — triaging tasks, drafting messages, scheduling activities, and researching context — while keeping all personal data local and consent-gated.**

Built for the **Google × Kaggle AI Agents Intensive (Vibe Coding) Capstone** | **Track: Concierge Agents**

---

## 🎯 The Problem

Busy professionals juggle dozens of tasks, messages, and meetings every week.
Existing AI assistants either:
- Auto-collect personal data without asking 🔓
- Require multiple separate apps for different needs 📱📱📱
- Lack the intelligence to prioritize and plan holistically 🤷

**WeekPilot** solves this with a single, privacy-first AI concierge that handles
your entire week — while keeping YOU in control of your data.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📋 **Task Triage** | Eisenhower-matrix prioritization (urgent × important) |
| ✉️ **Message Drafting** | Tone-aware emails/chat/SMS with human approval |
| 📅 **Schedule Planning** | Weather-aware weekly time-blocking |
| 🔍 **Research Assistant** | Google Search-grounded meeting prep |
| 🔒 **Privacy-First** | Consent-gated memory — asks before remembering |
| 🛡️ **Security-Hardened** | STRIDE threat model, PII redaction, injection defense |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  👤 User Input                       │
│                       │                              │
│              🎯 WeekPilot Orchestrator               │
│            (LLM-based intent routing)                │
│         ┌─────┬──────┬──────┬──────┐                │
│         ▼     ▼      ▼      ▼      │                │
│    📋 Task  ✉️ Msg  📅 Sched 🔍 Research            │
│    Triage  Drafter  Planner  Agent                   │
│         │     │      │      │                        │
│    ┌────┴─────┴──────┴──────┴────┐                  │
│    │      🔧 Tool Layer           │                  │
│    │  Custom Functions │ Search   │                  │
│    │  Weather REST API │ CodeExec │                  │
│    └──────────┬───────────────────┘                  │
│    ┌──────────┴───────────────────┐                  │
│    │     🛡️ Security Layer        │                  │
│    │  Callbacks │ PII Detection   │                  │
│    │  Guardrails│ Consent Gating  │                  │
│    └──────────┬───────────────────┘                  │
│    ┌──────────┴───────────────────┐                  │
│    │     🧠 Memory Layer          │                  │
│    │  Session State (short-term)  │                  │
│    │  Consent-Gated (long-term)   │                  │
│    └──────────────────────────────┘                  │
└─────────────────────────────────────────────────────┘
```

### Why Multi-Agent?

Each specialist owns a **distinct cognitive domain** with different tools,
instructions, and output schemas. A monolithic agent would conflate these
concerns. The orchestrator pattern keeps each agent focused, testable,
and adhering to least-privilege.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google AI Studio API key ([get one free](https://aistudio.google.com/apikey))

### Setup (one command)
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/weekpilot.git
cd weekpilot

# Create venv and install
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt

# Configure API key
copy .env.example .env       # Windows
# cp .env.example .env        # macOS/Linux
# Then edit .env and add your GOOGLE_API_KEY (never commit .env)
```

### Run
```bash
# Launch the ADK web UI
adk web weekpilot/

# Or run the CLI
adk run weekpilot/

# Run tests
pytest tests/ -v

# Run evaluation
python eval/run_eval.py

# Run security scan
python scripts/security_scan.py
```

---

## 🔒 Security Design

WeekPilot implements security as code, not an afterthought:

| Control | Implementation |
|---------|---------------|
| **Input validation** | All user input sanitized, length-limited, injection patterns blocked |
| **Tool allow-listing** | Only 14 whitelisted tools can execute; unknown tools are blocked |
| **PII redaction** | Emails, phones, SSNs detected and scrubbed from logs and outputs |
| **Consent gating** | Sensitive data requires explicit user approval before persistence |
| **Secret management** | Zero hardcoded secrets; `.env` only; pre-commit scanning |
| **Output scanning** | LLM responses scanned for leaked API keys before delivery |
| **Human-in-the-loop** | Required for message approval, task deletion, data persistence |

See [STRIDE.md](STRIDE.md) for the full threat model.

---

## 🧪 Testing

```bash
# All tests
pytest tests/ -v

# Security tests only
pytest tests/test_security.py -v

# Structural evaluation (no API key needed)
python eval/run_eval.py

# Live evaluation (requires API key)
python eval/run_eval.py --live --k 3
```

---

## 📁 Project Structure

```
weekpilot/
├── agent.py              # Root agent (ADK entry point)
├── agents/               # 4 specialist sub-agents
├── tools/                # 12+ custom function tools
├── mcp_server/           # MCP server: public-data tools (weather, date/time) over stdio
├── security/             # Callbacks, PII, guardrails, consent
├── memory/               # Consent-gated memory service
├── models/               # Pydantic schemas (data contracts)
└── observability/        # Structured logging with PII redaction
tests/                    # pytest test suite (tools, security, agents, memory)
eval/                     # Evaluation cases and runner
docs/                     # Kaggle write-up, video script, rationale
scripts/                  # Security scanning
```

---

## 📜 Course Concepts Demonstrated

| # | Concept | Where |
|---|---------|-------|
| 1 | Multi-Agent System (ADK) | Orchestrator + 4 specialists |
| 2 | MCP Server | `mcp_server/` exposes public-data tools (weather, date/time) over stdio; consumed via ADK `McpToolset` |
| 3 | Agent Tools | 12+ custom + Google Search + REST API |
| 4 | Context Engineering | Session state + consent-gated long-term memory |
| 5 | Security | STRIDE, 4 callbacks, PII detection, consent gating |
| 6 | Deployability | Clean structure, one-command setup, pinned deps |

---

## 📄 License

This project is licensed under [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Built with ❤️ for the Google × Kaggle AI Agents Intensive (Vibe Coding) Capstone.
