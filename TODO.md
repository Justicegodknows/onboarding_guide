# TODO - Nemoclaw mode implementation (sandbox: exist)

- [x] Inspect backend auth/retrieval/router files for integration points (`main.py`, `chat.py`, `security.py`, `rag_chain.py`, `rag_service.py`, schemas, tests).
- [x] Add Nemoclaw agent chat schemas in `rag_backend/app/models/schemas.py`:
  - `AgentChatRequest { message, conversation_id }`
  - `AgentChatResponse { answer, sources[] }`
  - source item model with `title`, `source`, `chunk_id`.
- [x] Add RBAC-aware retrieval helper reusing existing Chroma/RAG pipeline and returning context + sources.
- [x] Add Nemoclaw adapter service for sandbox `exist` with:
  - allowlisted read-only tool routing
  - timeout + resilient fallback behavior
  - sanitized error logging.
- [x] Add new FastAPI router `POST /agent/chat` with JWT dependency and RBAC claim usage.
- [x] Register the new router in `rag_backend/app/main.py`.
- [x] Add backend tests:
  - rejects missing/invalid JWT on `/agent/chat`
  - enforces RBAC retrieval boundaries by department.
- [x] Add minimal Next.js switch/toggle for "Nemoclaw mode" in chat flow.
- [x] Add frontend API helper for `/agent/chat` and keep existing chat path default.
- [x] Add/update configuration docs for `NEMOCLAW_SANDBOX_NAME=exist` and any required Nemoclaw runtime vars.
- [x] Add short local run notes + curl example for `/agent/chat`.

## Implementation Complete

All tasks completed. The Nemoclaw mode has been implemented with the following components:

### Backend (FastAPI)
- New router `/agent/chat` in `rag_backend/app/routers/agent.py`
- Agent chat request/response schemas in `rag_backend/app/models/schemas.py`
- RBAC-aware retrieval in `rag_backend/app/services/agent_retrieval.py`
- Nemoclaw adapter service in `rag_backend/app/services/nemoclaw_adapter.py`
- Configuration added to `rag_backend/app/core/config.py`

### Frontend (Next.js)
- Nemoclaw mode toggle in ChatBox component
- API helper function in `app/api/backend.ts`

### Tests
- Backend tests in `rag_backend/tests/test_agent_chat.py`

### How to Run Locally
1. Start backend: `cd rag_backend && uvicorn app.main:app --reload`
2. Start Nemoclaw sandbox (exist) if needed
3. Call `/agent/chat` with curl:
   ```bash
   curl -X POST http://localhost:8000/agent/chat \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{"message": "What is onboarding?", "conversation_id": null}'
