#mcp_orchestrator-main/apps/orchestrator/app/orchestration.py


# ============================================================
#   MCP Orchestrator — Simple Stateful Food Ordering Flow
#   MULTI-SESSION SAFE VERSION (Option A)
# ============================================================

from __future__ import annotations

from datetime import datetime, timezone

from .models import OrchestratorRequest, OrchestratorResponse, MemorySnapshot
from .session_context import Message, new_session_context
from .memory_store import MemoryStore


class AgentCore:
    """Agent Core handling state + memory + the simple food flow."""

    def __init__(self, store: MemoryStore):
        self.store = store

    async def handle(self, req: OrchestratorRequest) -> OrchestratorResponse:
        # ============================================================
        # MULTI-SESSION HANDLING (Option A: client-generated session)
        # ============================================================
        session_id = req.session_id or f"{req.user_id}:{req.channel}"

        # Load existing or create new session context
        ctx = await self.store.load_context(session_id, req.user_id, req.channel)

        # Track whether the session should reset after this reply
        reset_after_reply = False

        # Timestamp update
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

        # 1) Start food order
        if ctx.state.flow is None and any(
            kw in text_lower for kw in ["order", "food", "pizza", "burger", "menu", "cravings"]
        ):
            ctx.state.flow = "food_order"
            ctx.state.step = "ask_category"
            ctx.state.flags["awaiting_category"] = True

            reply_text = (
                "Nice, let's order some food!\n"
                "What type of food would you like? (pizza, burger, ramen, salad, etc.)"
            )

        # 2) Ask category
        elif ctx.state.flow == "food_order" and ctx.state.step == "ask_category":
            ctx.state.scratchpad["category"] = req.text
            ctx.state.step = "collect_items"
            ctx.state.flags["awaiting_category"] = False
            ctx.state.flags["awaiting_items"] = True

            reply_text = (
                f"Great, {req.text}!\n"
                "What items would you like to order? (e.g. '1 pepperoni pizza, 1 garlic bread')"
            )

        # 3) Collect food items
        elif ctx.state.flow == "food_order" and ctx.state.step == "collect_items":
            ctx.state.scratchpad["items"] = req.text
            ctx.state.step = "ask_address"
            ctx.state.flags["awaiting_items"] = False
            ctx.state.flags["awaiting_address"] = True

            reply_text = "Got it! What's the delivery address?"

        # 4) Collect address
        elif ctx.state.flow == "food_order" and ctx.state.step == "ask_address":
            ctx.state.scratchpad["address"] = req.text
            ctx.state.step = "ask_phone"
            ctx.state.flags["awaiting_address"] = False
            ctx.state.flags["awaiting_phone"] = True

            reply_text = "Great — and what phone number should the driver call?"

        # 5) Collect phone
        elif ctx.state.flow == "food_order" and ctx.state.step == "ask_phone":
            ctx.state.scratchpad["phone"] = req.text
            ctx.state.step = "confirm_order"
            ctx.state.flags["awaiting_phone"] = False
            ctx.state.flags["awaiting_confirmation"] = True

            category = ctx.state.scratchpad.get("category", "")
            items = ctx.state.scratchpad.get("items", "")
            address = ctx.state.scratchpad.get("address", "")
            phone = ctx.state.scratchpad.get("phone", "")

            reply_text = (
                "Here’s your full order summary:\n"
                f"- Category: {category}\n"
                f"- Items: {items}\n"
                f"- Address: {address}\n"
                f"- Phone: {phone}\n\n"
                "Would you like to place this order? Yes or No?"
            )

        # 6) Confirm order
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

                # Reset the session AFTER this reply
                reset_after_reply = True

            elif "no" in text_lower:
                ctx.state.flow = None
                ctx.state.step = None
                ctx.state.flags.clear()
                ctx.state.scratchpad.clear()

                reply_text = (
                    "Okay, the order is canceled. "
                    "If you'd like to order again, just say so!"
                )
            else:
                reply_text = "Please answer with 'yes' or 'no'."

        # ============================================================
        #  SIMPLE STATEFUL FOOD ORDERING FLOW (END)
        # ============================================================

        else:
            # Fallback smalltalk / echo
            if any(greet in text_lower for greet in ["hello", "hi", "hey"]):
                reply_text = f"Hello, {req.user_id}! (from MCP Orchestrator)"
            else:
                reply_text = f"Echo from orchestrator: {req.text}"

        # Append agent message
        agent_msg = Message(role="agent", text=reply_text, timestamp=now)
        ctx.short_term.history.append(agent_msg)

        # Save updated context state
        await self.store.save_context(ctx)

        # Reset after reply if flagged
        if reset_after_reply:
            fresh = new_session_context(
                session_id=session_id,
                user_id=req.user_id,
                channel=req.channel,
            )
            await self.store.save_context(fresh)

        # Build memory snapshot
        snapshot = MemorySnapshot(
            session_id=session_id,
            turn_count=ctx.short_term.turn_count,
        )

        debug = {
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
