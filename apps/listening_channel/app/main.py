
from fastapi import FastAPI, HTTPException
import httpx

from .config import get_settings
from .models import IncomingEvent, ForwardedResponse

settings = get_settings()
app = FastAPI(title=settings.APP_NAME, version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok", "block": "listening_channel"}

@app.post("/events/incoming", response_model=ForwardedResponse)
async def handle_incoming(event: IncomingEvent):
    """Receive an incoming event and forward it to Block 2 (MCP Orchestrator)."""
    payload = {
        "channel": event.channel,
        "user_id": event.user_id,
        # Session ID can be provided by caller later; for now we derive a simple one
        "session_id": f"{event.user_id}:{event.channel}",
        "text": event.text,
        "metadata": event.metadata or {},
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(settings.ORCHESTRATOR_URL, json=payload)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to reach orchestrator: {e}")

    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}

    return ForwardedResponse(
        status="ok",
        reply=data,
    )
