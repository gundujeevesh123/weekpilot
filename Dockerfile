# =============================================================================
# WeekPilot — single-image deploy (React UI + FastAPI + ADK agent)
# Build:  docker build -t weekpilot .
# Run:    docker run -p 8000:8000 -e GOOGLE_API_KEY=... weekpilot
# One public URL serves both the UI and the /api so anyone can use it.
# =============================================================================

# ---- Stage 1: build the React frontend -------------------------------------
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python runtime ------------------------------------------------
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY weekpilot/ ./weekpilot/
COPY backend/ ./backend/

# Built UI from stage 1 (served by FastAPI at "/")
COPY --from=frontend /app/frontend/dist ./frontend/dist

EXPOSE 8000
# Hosts (Render/Railway/Fly) inject $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
