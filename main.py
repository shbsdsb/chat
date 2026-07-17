"""
AI Chat Desktop — Python Backend Entry Point
============================================
FastAPI server providing health check, chat, and session management APIs
for the Electron + Vue 3 AI Chat desktop application.

Run:
    python main.py
    uvicorn main:app --host 127.0.0.1 --port 8765 --reload
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()

HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8765"))

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Payload sent by the frontend when the user sends a message."""

    message: str = Field(..., min_length=1, description="User message text.")
    session_id: str = Field(..., min_length=1, description="Target session identifier.")


class ChatResponse(BaseModel):
    """Payload returned to the frontend after processing a chat message."""

    response: str = Field(..., description="AI response text (placeholder for now).")
    session_id: str = Field(..., description="Echoed session identifier.")


class SessionMeta(BaseModel):
    """Public metadata about a single conversation session."""

    id: str
    title: str
    created_at: str


class SessionCreateRequest(BaseModel):
    """Optional payload for session creation (title override)."""

    title: str = Field("新会话", min_length=1, max_length=200)


class SessionCreateResponse(BaseModel):
    """Returned after a new session is created."""

    id: str
    title: str
    created_at: str


# ---------------------------------------------------------------------------
# In-Memory Store (no database for now)
# ---------------------------------------------------------------------------

# Internal representation: id → {title, created_at (ISO string)}
_sessions: dict[str, dict[str, str]] = {}


def _now_iso() -> str:
    """Return current UTC timestamp as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Chat Desktop — Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow local Electron dev & production origins
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",       # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:8765",       # served static in production
        "http://127.0.0.1:8765",
        "app://.",                     # Electron production (file:// equivalent)
    ],
    allow_origin_regex=r"^file://.*$",  # Electron loads via file://
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Return server health status.

    Used by the Electron main process to verify the backend is alive
    before allowing the renderer to send requests.
    """
    return {"status": "ok"}


# -- Chat ---------------------------------------------------------------


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["Chat"],
    summary="Send a chat message and receive an AI response.",
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Accept a user message and return a **placeholder** AI response.

    In future iterations this endpoint will route to OpenAI, Ollama, or
    other local models depending on user configuration.
    """
    if request.session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found.",
        )

    placeholder = f"[AI response placeholder for: {request.message}]"
    return ChatResponse(response=placeholder, session_id=request.session_id)


# -- Sessions -----------------------------------------------------------


@app.get(
    "/sessions",
    response_model=list[SessionMeta],
    tags=["Sessions"],
    summary="List all conversation sessions.",
)
async def list_sessions() -> list[SessionMeta]:
    """Return every session, most-recently-created first."""
    sorted_ids = sorted(
        _sessions.keys(),
        key=lambda sid: _sessions[sid]["created_at"],
        reverse=True,
    )
    return [
        SessionMeta(
            id=sid,
            title=_sessions[sid]["title"],
            created_at=_sessions[sid]["created_at"],
        )
        for sid in sorted_ids
    ]


@app.post(
    "/sessions",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sessions"],
    summary="Create a new conversation session.",
)
async def create_session(body: SessionCreateRequest = SessionCreateRequest()) -> SessionCreateResponse:
    """Create a fresh session and return its metadata.

    The frontend calls this when the user clicks the "新建" button.
    """
    sid = uuid.uuid4().hex
    now = _now_iso()
    _sessions[sid] = {"title": body.title, "created_at": now}
    return SessionCreateResponse(id=sid, title=body.title, created_at=now)


@app.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Sessions"],
    summary="Delete a conversation session.",
)
async def delete_session(session_id: str) -> None:
    """Remove a session by its identifier.

    If the session does not exist the call still succeeds (idempotent).
    """
    _sessions.pop(session_id, None)


# ---------------------------------------------------------------------------
# Main Guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
