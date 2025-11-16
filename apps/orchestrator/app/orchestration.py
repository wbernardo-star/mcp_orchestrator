#MCP Orch Support Flow Python

from __future__ import annotations

from datetime import datetime, timezone

from .models import OrchestratorRequest, OrchestratorResponse, MemorySnapshot
from .session_context import Message, new_session_context
from .memory_store import MemoryStore


class AgentCore:
    """Agent Core handling state + memory + flows."""

    def __init__(self, store: MemoryStore):
        self.store = store

    async def handle(self, req: OrchestratorRequest) -> OrchestratorResponse:
        # Resolve session ID (can be passed in, or derived from user+channel)
        session_id = req.session_id or f"{req.user_id}:{req.channel}"

        # Load existing or new session context
        ctx = await self.store.load_context(session_id, req.user_id, req.channel)

        # Track whether we should reset everything AFTER this reply
        reset_after_reply = False

        # Update timestamps
        now = datetime.now(timezone.utc)
        ctx.session.last_active_at = now

        # Append user message to short-term memory
        user_msg = Message(role="user", text=req.text, timestamp=now)
        ctx.short_term.history.append(user_msg)
        ctx.short_term.turn_count += 1
        ctx.short_term.last_user_message_at = now

        # ============================================================
        #  SIMPLE STATEFUL FOOD ORDERING FLOW (BEGIN)
        # ============================================================
        text_lower = req.text.lower().strip()

        # 1) Start the food ordering flow
        if ctx.state.flow is None and any(
            kw in text_lower for kw in ["order", "food", "pizza", "burger", "menu", "cravings"]
        ):
            ctx.state.flow = "food_order"
            ctx.state.step = "ask_category"
            ctx.state.flags["awaiting_category"] = True
            reply_text = (
                "Nice, let's order some food!\n"
                "What type of food would you like? (example. pizza, burger, salad, chicken, ramen)"
            )

        # 2) Ask category (pizza, burger, etc.)
        elif ctx.state.flow == "food_order" and ctx.state.step == "ask_category":
            ctx.state.scratchpad["category"] = req.text
            ctx.state.step = "collect_items"
            ctx.state.flags["awaiting_category"] = False
            ctx.state.flags["awaiting_items"] = True
            reply_text = (
                f"Great, {req.text}!\n"
                "What food items would you like to order? "
                "Example: '1 large pepperoni, 1 garlic bread'."
            )

        # 3) Collect food items
        elif ctx.state.flow == "food_order" and ctx.state.step == "collect_items":
            ctx.state.scratchpad["items"] = req.text
            ctx.state.step = "ask_address"
            ctx.state.flags["awaiting_items"] = False
            ctx.state.flags["awaiting_address"] = True
            reply_text = (
                "Got it!\n"
                "Next, what's the delivery address?"
            )

        # 4) Ask for address
        elif ctx.state.flow == "food_order" and ctx.state.step == "ask_address":
            ctx.state.scratchpad["address"] = req.text
            ctx.state.step = "ask_phone"
            ctx.state.flags["awaiting_address"] = False
            ctx.state.flags["awaiting_phone"] = True
            reply_text = (
                "Great — and what phone number should the driver call?"
            )

        # 5) Ask for phone number
        elif ctx.state.flow == "food_order" and ctx.state.step == "ask_phone":
            ctx.state.scratchpad["phone"] = req.text
            ctx.state.step = "confirm_order"
            ctx.state.flags["awaiting_phone"] = False
            ctx.state.flags["awaiting_confirmation"] = True

            category = ctx.state.scratchpad.get("category", "food")
            items = ctx.state.scratchpad.get("items", "")
            address = ctx.state.scratchpad.get("address", "")
            phone = ctx.state.scratchpad.get("phone", "")

            reply_text = (
                "Here’s your full order summary:\n"
                f"- Category: {category}\n"
                f"- Items: {items}\n"
                f"- Address: {address}\n"
                f"- Phone: {phone}\n\n"
                "Would you like to place this order? Please say Yes to confirm or No to cancel."
            )

        # 6) Final confirmation
        elif ctx.state.flow == "food_order" and ctx.state.step == "confirm_order":
            if "yes" in text_lower:
                ctx.state.step = "order_placed"
                ctx.state.flags["awaiting_confirmation"] = False

                category = ctx.state.scratchpad.get("category")
                items = ctx.state.scratchpad.get("items")
                address = ctx.state.scratchpad.get("address")
                phone = ctx.state.scratchpad.get("phone")

                reply_text = (
                    "Your food order has been placed!\n"
                    f"- Category: {category}\n"
                    f"- Items: {items}\n"
                    f"- Address: {address}\n"
                    f"- Phone: {phone}\n\n"
                    "Thanks for ordering!"
                )

                # Mark that we should reset the whole session AFTER this reply
                reset_after_reply = True

            elif "no" in text_lower:
                # Cancel the order and reset flow + scratchpad
                ctx.state.flow = None
                ctx.state.step = None
                ctx.state.flags.clear()
                ctx.state.scratchpad.clear()

                reply_text = (
                    "Okay, I've canceled the order. If you want to try again, "
                    "just say you want to order food."
                )
            else:
                reply_text = "Please answer with 'yes' or 'no'."

        # ============================================================
        #  SIMPLE STATEFUL FOOD ORDERING FLOW (END)
        # ============================================================

        # Fallback: greetings & echo for anything outside the flow
        else:
            if any(g in text_lower for g in ["hello", "hi", "hey"]):
                reply_text = f"Hello, {req.user_id}! (from MCP Orchestrator)"
            else:
                reply_text = f"Echo from orchestrator: {req.text}"

        # Append agent message to short-term memory
        agent_msg = Message(role="agent", text=reply_text, timestamp=now)
        ctx.short_term.history.append(agent_msg)

        # Save updated context (so the client sees the latest state)
        await self.store.save_context(ctx)

        # If requested, immediately reset the session, memory, and state
        if reset_after_reply:
            fresh_ctx = new_session_context(
                session_id=session_id,
                user_id=req.user_id,
                channel=req.channel,
            )
            await self.store.save_context(fresh_ctx)

        # Snapshot of memory (for the client)
        snapshot = MemorySnapshot(
            session_id=ctx.session.session_id,
            turn_count=ctx.short_term.turn_count,
        )

        debug = {
            "version": ctx.meta.version,
            "channel": ctx.session.channel,
            "flow": ctx.state.flow,
            "step": ctx.state.step,
        }

        return OrchestratorResponse(
            decision="reply",
            reply_text=reply_text,
            memory_snapshot=snapshot,
            state=ctx.state,
            debug=debug,
        )


