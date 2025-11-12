
from __future__ import annotations

from datetime import datetime, timezone

from .models import OrchestratorRequest, OrchestratorResponse, MemorySnapshot
from .session_context import SessionContext, Message
from .memory_store import MemoryStore


class AgentCore:
    """Simple Agent Core using SessionContext.

    This is where you later integrate:
    - MCP tools
    - LLM calls
    - Multi-step workflows

    For now, it:
    - loads SessionContext
    - updates history and turn_count
    - replies with a simple greeting/echo
    """

    def __init__(self, store: MemoryStore):
        self.store = store

    async def handle(self, req: OrchestratorRequest) -> OrchestratorResponse:
        # Resolve session_id
        session_id = req.session_id or f"{req.user_id}:{req.channel}"

        # Load existing or new context
        ctx = await self.store.load_context(session_id, req.user_id, req.channel)

        # Update timestamps
        now = datetime.now(timezone.utc)
        ctx.session.last_active_at = now

        # Append user message
        user_msg = Message(role="user", text=req.text, timestamp=now)
        ctx.short_term.history.append(user_msg)
        ctx.short_term.turn_count += 1
        ctx.short_term.last_user_message_at = now

        # Very simple decision logic
        text_lower = req.text.lower().strip()
        if any(g in text_lower for g in ["hello", "hi", "hey"]):
            reply_text = f"Hello, {req.user_id}! (from MCP Orchestrator)"
        else:
            reply_text = f"Echo from orchestrator: {req.text}"

        # Append agent message
        agent_msg = Message(role="agent", text=reply_text, timestamp=now)
        ctx.short_term.history.append(agent_msg)

        # Save context
        await self.store.save_context(ctx)

        snapshot = MemorySnapshot(
            session_id=ctx.session.session_id,
            turn_count=ctx.short_term.turn_count,
        )
        debug = {
            "version": ctx.meta.version,
            "channel": ctx.session.channel,
        }
        return OrchestratorResponse(
            decision="reply",
            reply_text=reply_text,
            memory_snapshot=snapshot,
            debug=debug,
        )
