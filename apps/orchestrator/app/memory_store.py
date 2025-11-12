
from __future__ import annotations

from typing import Dict
from .session_context import SessionContext, new_session_context


class MemoryStore:
    """In-memory implementation of a SessionContext store.

    Later you can replace this with Redis/Postgres, but keep the same interface.
    """
    def __init__(self):
        self._store: Dict[str, SessionContext] = {}

    async def load_context(self, session_id: str, user_id: str, channel: str) -> SessionContext:
        if session_id in self._store:
            return self._store[session_id]
        ctx = new_session_context(session_id=session_id, user_id=user_id, channel=channel)
        self._store[session_id] = ctx
        return ctx

    async def save_context(self, context: SessionContext) -> None:
        sid = context.session.session_id
        self._store[sid] = context
