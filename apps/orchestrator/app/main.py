
from fastapi import FastAPI

from .config import get_settings
from .models import OrchestratorRequest, OrchestratorResponse
from .memory_store import MemoryStore
from .orchestration import AgentCore

settings = get_settings()
app = FastAPI(title=settings.APP_NAME, version="0.1.0")

_store = MemoryStore()
_agent = AgentCore(store=_store)

@app.get("/health")
async def health():
    return {"status": "ok", "block": "mcp_orchestrator"}

@app.post("/orchestrate", response_model=OrchestratorResponse)
async def orchestrate(request: OrchestratorRequest):
    return await _agent.handle(request)
