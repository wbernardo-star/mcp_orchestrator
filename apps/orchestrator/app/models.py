
from typing import Any, Dict, Optional
from pydantic import BaseModel


class OrchestratorRequest(BaseModel):
    channel: str
    user_id: str
    text: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MemorySnapshot(BaseModel):
    session_id: str
    turn_count: int


class OrchestratorResponse(BaseModel):
    decision: str
    reply_text: str
    memory_snapshot: MemorySnapshot
    debug: Dict[str, Any]
