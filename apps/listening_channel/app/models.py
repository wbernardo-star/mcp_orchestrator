
from typing import Any, Dict, Optional
from pydantic import BaseModel

class IncomingEvent(BaseModel):
    channel: str
    user_id: str
    text: str
    metadata: Optional[Dict[str, Any]] = None

class ForwardedResponse(BaseModel):
    status: str
    reply: Dict[str, Any]
