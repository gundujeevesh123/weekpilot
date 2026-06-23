"""
WeekPilot Web Backend — a thin, secure FastAPI wrapper around the ADK agent.

It exposes two endpoints the React frontend uses:
    GET  /api/health  -> liveness probe
    POST /api/chat    -> { message, session_id? } -> { session_id, reply }

SECURITY / PRIVACY (data confidentiality + integrity)
- The Gemini API key is loaded **server-side** (from ``.env`` via the agent) and
  is NEVER sent to the browser. The frontend only ever transmits the user's
  message text.
- **CORS is locked** to explicit origins (``WEEKPILOT_CORS_ORIGINS``), never "*".
- Input is **length-limited**; the agent's own guardrails + PII-redaction
  callbacks still run on every request and response.
- Only the final assistant text and an opaque session id are returned — no
  internal events, traces, or stack traces leak to the client.
- Sessions are in-memory and keyed by a random UUID; personal data stays in the
  process and is not persisted to disk.
"""

from __future__ import annotations

import os
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google.genai import types
from google.adk.runners import InMemoryRunner

from weekpilot.agent import root_agent

# A single reusable runner with lightweight in-memory services.
_runner = InMemoryRunner(agent=root_agent)
APP_NAME = _runner.app_name
_USER_ID = "web-user"
_MAX_MESSAGE_CHARS = 2000


def _allowed_origins() -> list[str]:
    """CORS allow-list. Override with WEEKPILOT_CORS_ORIGINS (comma-separated)."""
    raw = os.environ.get(
        "WEEKPILOT_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


class ChatRequest(BaseModel):
    """Incoming chat message from the browser."""

    message: str = Field(..., min_length=1, max_length=_MAX_MESSAGE_CHARS)
    session_id: str | None = Field(default=None, max_length=64)


class ChatResponse(BaseModel):
    """The assistant's reply plus the session id to continue the conversation."""

    session_id: str
    reply: str


app = FastAPI(title="WeekPilot API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
async def health() -> dict:
    """Liveness probe used by the frontend before the first message."""
    return {"status": "ok", "app": APP_NAME}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Run one turn of the WeekPilot agent and return the final reply."""
    text = req.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id = req.session_id or str(uuid.uuid4())

    # Create the session on the first message of a conversation.
    existing = await _runner.session_service.get_session(
        app_name=APP_NAME, user_id=_USER_ID, session_id=session_id
    )
    if existing is None:
        await _runner.session_service.create_session(
            app_name=APP_NAME, user_id=_USER_ID, session_id=session_id
        )

    message = types.Content(role="user", parts=[types.Part(text=text)])
    reply = ""
    try:
        async for event in _runner.run_async(
            user_id=_USER_ID, session_id=session_id, new_message=message
        ):
            if event.is_final_response() and event.content and event.content.parts:
                reply = event.content.parts[0].text or reply
    except Exception:
        # Don't leak internals; the model retry/backoff already handled transient
        # 503s, so a failure here means the assistant is genuinely busy/unavailable.
        raise HTTPException(
            status_code=503,
            detail="The assistant is busy right now. Please try again in a moment.",
        )

    return ChatResponse(session_id=session_id, reply=reply or "(no response)")
