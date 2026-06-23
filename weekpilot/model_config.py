"""
Central Gemini model configuration for every WeekPilot agent.

WHY THIS EXISTS
- **Resilience (avoid errors):** Gemini occasionally returns a transient
  ``503 UNAVAILABLE`` ("model is experiencing high demand"). We attach automatic
  retry with exponential backoff so those spikes self-heal instead of surfacing
  as an error to the user.
- **One knob (cost / flexibility):** every agent builds its model here, so you
  can switch the whole app to a cheaper or more-available model with a single
  environment variable — no code edits.

Override the model for the entire app:
    setx WEEKPILOT_MODEL gemini-2.5-flash-lite      (Windows, then reopen shell)
    export WEEKPILOT_MODEL=gemini-2.0-flash         (macOS/Linux)
"""

from __future__ import annotations

import os

from google.adk.models.google_llm import Gemini
from google.genai import types

# Proven default; override via WEEKPILOT_MODEL. Lighter/cheaper, often more
# available alternatives: "gemini-2.5-flash-lite", "gemini-2.0-flash".
DEFAULT_MODEL = "gemini-2.5-flash"

# Retry transient rate-limit / server-overload errors with exponential backoff.
_RETRY_OPTIONS = types.HttpRetryOptions(
    attempts=4,            # original try + 3 retries
    initial_delay=1.0,     # seconds before the first retry
    max_delay=20.0,        # cap between retries
    exp_base=2.0,          # 1s, 2s, 4s, ...
    http_status_codes=[429, 500, 502, 503, 504],
)


def model_name() -> str:
    """Return the model id used by all agents (``WEEKPILOT_MODEL`` or default)."""
    return os.environ.get("WEEKPILOT_MODEL", DEFAULT_MODEL)


def build_model() -> Gemini:
    """Build a Gemini model configured with automatic retry/backoff.

    Returns:
        A ``google.adk.models.Gemini`` instance shared-config across agents.
    """
    return Gemini(model=model_name(), retry_options=_RETRY_OPTIONS)
