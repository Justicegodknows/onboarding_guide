---
name: task-execution
description: Execute backend tasks in the VaultMind system — ingestion, document processing, API calls, or service interactions — without breaking the running system. Use when the agent needs to trigger ingestion, run a scraper, interact with RAGService, call the ingest API, manage knowledge sources, or orchestrate multi-step backend operations. Triggers on phrases like "ingest", "index", "scrape", "run the pipeline", "trigger ingestion", "add documents to", "update the knowledge base", or "process files".
---

You are executing a task inside the VaultMind backend. The system is live and on-premises. Be methodical, minimal, and safe. Verify before acting; report clearly after.

## System topology (understand before touching anything)

```
/rag_backend/
├── app/
│   ├── main.py              — FastAPI app, all routers registered here
│   ├── core/config.py       — Settings loaded from rag_backend/.env
│   ├── routers/ingest.py    — POST /api/v1/ingest/?source=...  (unprotected)
│   └── services/
│       ├── rag_service.py          — RAGService: embed + store + retrieve
│       ├── ingest_chunks.py        — Orchestrates all ingestion paths
│       ├── youtube_knowledge.py    — yt-dlp (primary) + RSS (fallback)
│       ├── google_drive_knowledge.py
│       ├── local_folder_knowledge.py
│       └── chunk_documents.py      — chunk_text(text, chunk_size)
└── chroma_db/               — DO NOT touch binary files directly
```

## Ingestion task checklist

Run through this before triggering any ingestion:

1. **Identify the source** — which knowledge source is being updated?

| source param | What it ingests | Key env vars |
|---|---|---|
| `youtube` | `@e.u.z-am-deister` channel transcripts | `YOUTUBE_CHANNEL`, `YOUTUBE_MAX_VIDEOS`, `YOUTUBE_CHUNK_SIZE` |
| `google_drive` | Google Drive folder (PDFs, DOCX, XLSX, TXT) | `GOOGLE_DRIVE_FOLDER_ID`, `GOOGLE_DRIVE_API_KEY` |
| `local_folder` | `rag_backend/docs/EUZ Project/` on disk | `EUZ_DOCS_FOLDER` or `folder_path` query param |
| `local` | `help/chunks.json` (static fallback) | — |

2. **Verify configuration** — check `rag_backend/.env` for required vars before calling.
3. **Trigger via API** (preferred — avoids import side effects):

```bash
# YouTube channel ingestion
curl -X POST "http://localhost:8000/api/v1/ingest/?source=youtube"

# Google Drive
curl -X POST "http://localhost:8000/api/v1/ingest/?source=google_drive"

# Local EUZ docs folder
curl -X POST "http://localhost:8000/api/v1/ingest/?source=local_folder"

# Override channel for one-off ingestion
curl -X POST "http://localhost:8000/api/v1/ingest/?source=youtube&youtube_channel=https://www.youtube.com/@handle/videos"
```

4. **Read the response** — check `status`, `ingested`, `errors_or_duplicates`, and `meta.scrape_method`.
5. **Verify chunks landed** — spot-check via `RAGService.retrieve()` with a query that should match the new content.

## Direct service execution (when API is not available)

```python
from app.services.ingest_chunks import ingest_chunks
result = ingest_chunks(source="youtube", allow_local_fallback=False)
print(result)
```

- Set `allow_local_fallback=False` when you want hard failures instead of silent fallback to `help/chunks.json`.
- Always print or log the result dict — it contains `chunk_count`, `ingested`, and `meta`.

## RAGService usage rules

```python
from app.services.rag_service import RAGService
rag = RAGService()

# Ingest a single chunk dict
rag.ingest({"source": "...", "chunk_id": "...", "text": "...", "topic": "...", "tags": "..."})

# Retrieve (always use this — never access chroma_db directly)
results = rag.retrieve(query="...", top_k=5)
```

- `chunk_id` prevents duplicate ingestion — always set it for programmatic ingestion.
- Embeddings use `input_type: "passage"` for ingest and `input_type: "query"` for retrieval automatically.

## ChromaDB rules (non-negotiable)

- **Never modify binary files** in `chroma_db/` (`*.bin`, `*.pickle`).
- **Never delete `chroma.sqlite3`** without a confirmed backup and user approval.
- Always interact through `RAGService`. Direct ChromaDB calls bypass the embedding model contract.

## Safety gates before executing

| Check | How |
|---|---|
| Is the backend container running? | `curl http://localhost:8000/health` |
| Are env vars set? | Read `rag_backend/.env` before assuming defaults |
| Will this overwrite existing data? | `chunk_id`-based deduplication means re-ingesting the same chunk updates, not duplicates — but verify with a test call first |
| Is the embedding model consistent? | `NVIDIA_EMBED_MODEL` in `.env` must match what was used to build the current index |

## Reporting after task execution

Always end with:
- **What ran**: source, method (yt-dlp/RSS/Drive/etc.), timestamp.
- **Numbers**: videos/files seen, chunks ingested, errors or duplicates.
- **Next step**: how to verify the content is retrievable (example query to run).
- **What was not done**: if the task was partial, say so explicitly.

## Do not

- Modify code in `rag_backend/` as part of a routine ingestion task — that's a code change, not a task execution.
- Run `rm`, `truncate`, or any destructive command in `rag_backend/` without explicit user confirmation.
- Assume a silent 200 response means data landed — read the response body.
- Retry a failed ingestion in a loop — diagnose the error first.
