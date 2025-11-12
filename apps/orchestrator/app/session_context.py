
from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class Session(BaseModel):
    session_id: str
    user_id: str
    channel: str
    created_at: datetime
    last_active_at: datetime


class Message(BaseModel):
    role: Literal["user", "agent", "tool"]
    text: str
    timestamp: datetime
    tool_name: Optional[str] = None


class ShortTermMemory(BaseModel):
    history: List[Message] = Field(default_factory=list)
    turn_count: int = 0
    last_user_message_at: Optional[datetime] = None


class Fact(BaseModel):
    id: str
    type: str
    key: str
    value: Any
    created_at: datetime
    last_updated_at: datetime


class LongTermMemory(BaseModel):
    profile: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    facts: List[Fact] = Field(default_factory=list)


class State(BaseModel):
    flow: Optional[str] = None
    step: Optional[str] = None
    flags: Dict[str, Any] = Field(default_factory=dict)
    scratchpad: Dict[str, Any] = Field(default_factory=dict)


class Meta(BaseModel):
    version: str = "v1"
    debug: Dict[str, Any] = Field(default_factory=dict)


class SessionContext(BaseModel):
    session: Session
    short_term: ShortTermMemory
    long_term: LongTermMemory
    state: State
    meta: Meta


def new_session_context(session_id: str, user_id: str, channel: str) -> SessionContext:
    now = datetime.now(timezone.utc)
    session = Session(
        session_id=session_id,
        user_id=user_id,
        channel=channel,
        created_at=now,
        last_active_at=now,
    )
    return SessionContext(
        session=session,
        short_term=ShortTermMemory(),
        long_term=LongTermMemory(),
        state=State(),
        meta=Meta(),
    )
