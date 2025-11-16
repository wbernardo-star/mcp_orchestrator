#mcp_orchestrator-main/apps/orchestrator/app/orchestration.py


import json
from .models import OrchestratorRequest, OrchestratorResponse
from .memory_store import MemoryStore
from .session_context import SessionContext
from .llm_router import LLMBasedIntentRouter
from .state import FoodOrderStateMachine


class AgentCore:
    def __init__(self, store: MemoryStore):
        self.store = store
        self.router = LLMBasedIntentRouter()
        self.state_machine = FoodOrderStateMachine()

    async def handle(self, req: OrchestratorRequest) -> OrchestratorResponse:
        # ============================================================
        # SESSION MANAGEMENT — load or create per-client session
        # ============================================================
        session_id = req.session_id
        if not session_id:
            session_id = f"{req.user_id}:{req.channel}"

        ctx = await self.store.load_context(
            session_id=session_id,
            user_id=req.user_id,
            channel=req.channel
        )

        ctx.short_term.add_message(role="user", text=req.text)

        # ============================================================
        # LLM Router → classify intent
        # ============================================================
        intent_data = self.router.route(req.text, ctx)

        # ============================================================
        # STATE MACHINE → decide next step
        # ============================================================
        reply_text, session_done = self.state_machine.handle(intent_data, ctx)

        # Save message to context
        ctx.short_term.add_message(role="assistant", text=reply_text)

        # ============================================================
        # Persist updated memory/session
        # ============================================================
        await self.store.save_context(ctx)

        return OrchestratorResponse(
            reply_text=reply_text,
            session_id=session_id,
            user_id=req.user_id,
            debug={
                "intent": intent_data.intent,
                "items": intent_data.items,
                "session_done": session_done,
            },
            session_done=session_done
        )
