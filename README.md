
# MCP Monorepo – Listening Channel + MCP Orchestrator

- **MCP Orchestrator**
  - Owns **session, state, and memory**
  - Uses a concrete `SessionContext` struct internally
  - Returns decisions + replies back to the Listening Channel
  - Stubbed for MCP integration (you can plug in the `mcp` package later)

High-level data flow:

```text
[User / External System]
        ↓
[Listening Channel /External Systen]
        ↓ (normalized event)
 Block 2: MCP Orchestrator (Session + State + Memory)
```

This version uses **one repo**, **one virtualenv**, and **no Docker**.

---

## 1. Setup

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Optional: copy environment file

```bash
cp .env.example .env
```

---

## 2. Run the MCP Orchestrator

In one terminal:

```bash
source .venv/bin/activate
make run-orchestrator
# or, manually:
# uvicorn apps.orchestrator.app.main:app --reload --port 7002
```

Check health:

```bash
curl http://localhost:7002/health
```

---

---

## 4. End-to-end test

Call **Listen Channel**; it forwards to **MCP Orchestrator**, which manages `SessionContext`
for `user-123:web`:

```bash
curl -X POST http://localhost:7001/events/incoming   -H "Content-Type: application/json"   -d '{
    "channel": "web",
    "user_id": "user-123",
    "text": "hello orchestrator"
  }'
```

Expected shape:

```json
{
  "status": "ok",
  "reply": {
    "decision": "reply",
    "reply_text": "Hello, user-123! (from MCP Orchestrator)",
    "memory_snapshot": {
      "session_id": "user-123:web",
      "turn_count": 1
    },
    "debug": {
      "version": "v1",
      "channel": "web"
    }
  }
}
```

---

## 5. Project structure

```text
apps/
  orchestrator/              # Main MCP Orchestrator
    app/
      __init__.py
      main.py                # FastAPI app (MCP Orchestrator)
      config.py
      models.py              # Request/response for orchestrator API
      session_context.py     # SessionContext struct
      memory_store.py        # Simple in-memory store
      orchestration.py       # AgentCore using SessionContext
tests/
  test_orchestrator_health.py
```

---

## 6. Tests

```bash
source .venv/bin/activate
pytest -q
```

---

You can push this monorepo directly to GitHub and evolve both services
together while keeping a clean separation by folder.

