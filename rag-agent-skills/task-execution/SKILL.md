---
name: task-execution
description: Execute backend tasks in the VaultMind system — ingestion, document processing, computation, spreadsheet generation, or API calls — without breaking the running system. Use when the agent needs to trigger ingestion, run a scraper, interact with RAGService, call the ingest API, manage knowledge sources, orchestrate multi-step backend operations, evaluate calculations, generate Excel files, or process uploaded documents.
---

You are executing a task inside the VaultMind backend. The system is live and on-premises. Be methodical, minimal, and safe. Verify before acting; report clearly after.

## System topology (understand before touching anything)

```
/rag_backend/
├── app/
│   ├── main.py              — FastAPI app, all routers registered here
│   ├── core/config.py       — Settings loaded from rag_backend/.env
│   ├── routers/ingest.py    — POST /api/v1/ingest/?source=...  (unprotected)
│   ├── routers/trainer.py   — POST /api/v1/trainer/  (Q&A)
│   │                          POST /api/v1/trainer/upload  (document → text)
│   │                          GET  /api/v1/trainer/downloads/{filename}
│   └── services/
│       ├── rag_service.py          — RAGService: embed + store + retrieve
│       ├── trainer_agent.py        — TrainerSubAgent: tools + answer()
│       ├── ingest_chunks.py        — Orchestrates all ingestion paths
│       ├── youtube_knowledge.py    — yt-dlp (primary) + RSS (fallback)
│       ├── google_drive_knowledge.py
│       ├── local_folder_knowledge.py
│       └── chunk_documents.py      — chunk_text(text, chunk_size)
└── chroma_db/               — DO NOT touch binary files directly
```

────────────────────────────────────────

## Computation (`compute` tool)

Use the `compute` tool whenever the user asks for a numerical result — calculation, formula evaluation, unit conversion, percentage, or estimate.

**Trigger phrases**: "calculate", "how much is", "what is X times Y", "convert", "formula", "result of".

**What it supports**:
| Category | Supported |
|---|---|
| Arithmetic | `+`, `-`, `*`, `/`, `//`, `%`, `**` |
| Functions | `abs`, `round`, `min`, `max`, `sum`, `pow`, `sqrt`, `log`, `log10`, `sin`, `cos`, `tan`, `floor`, `ceil` |
| Constants | `pi`, `e` |

**What it does NOT support**: string ops, imports, loops, conditionals, variable assignment, or any Python statement.

**Usage pattern**:
```
compute(expression="(12.5 * 4) / 2")
→ { "expression": "(12.5 * 4) / 2", "result": 25 }

compute(expression="sqrt(144) + pi")
→ { "expression": "sqrt(144) + pi", "result": 15.14159... }
```

**Safety rules**:
- Never pass user-supplied strings directly without sanitizing — always pass the literal expression.
- Exponents are capped at 1000 to prevent runaway computation.
- If `error` key appears in the result, report it to the user and do not retry with a different expression without clarification.

**Response format**:
> The result of `{expression}` is **{result}**.

────────────────────────────────────────

## Excel sheet generation (`generate_excel` tool)

Use the `generate_excel` tool when the user requests a spreadsheet, data export, or structured table in Excel format.

**Trigger phrases**: "create an Excel file", "generate a spreadsheet", "export to Excel", "download as .xlsx", "make a table I can open in Excel".

**Tool signature**:
```
generate_excel(
    title="Report Title",
    headers=["Column A", "Column B", "Column C"],
    rows=[
        ["row1a", "row1b", 42],
        ["row2a", "row2b", 7.5],
    ]
)
```

**What the tool returns**:
```json
{
    "download_url": "/api/v1/trainer/downloads/<uuid>.xlsx",
    "filename": "<uuid>.xlsx",
    "rows_written": 2,
    "columns": 3
}
```

**Response format** — always give the user a clickable link:
> I've generated your Excel file. [Download {title}.xlsx]({download_url})
> It contains {rows_written} rows and {columns} columns.

**Rules**:
- Sheet title is trimmed to 31 characters (Excel limit) automatically.
- Files are ephemeral (stored in `/tmp/trainer_downloads/`). Warn the user to download promptly; they are not persisted across container restarts.
- If `error` key appears in the result, report it and ask the user whether to retry or proceed differently.
- Do not fabricate data — only create spreadsheets from data explicitly provided or retrieved via other tools.

────────────────────────────────────────

## Document processing via upload button

When a user uploads a document via the Trainer chat interface, the frontend:
1. POSTs the file to `POST /api/v1/trainer/upload`
2. Receives back the extracted text (max 12 000 chars; truncated flag if larger)
3. Prepends it to the next question sent to the Trainer:

```
[Attached document: filename.pdf (truncated)]

<extracted text>

---

<user question>
```

**As the Trainer agent, when you receive a message with this format**:
- Treat the attached document text as primary evidence for answering the question.
- If the document text is truncated, say so explicitly and note that only the first 12 000 characters were provided.
- Do NOT reference the document as a ChromaDB source — it was not embedded; it is session-scoped context only.
- Citation format: `[Uploaded: filename.pdf]` — do not invent page numbers.

**Supported upload formats**: PDF, DOCX, TXT, MD, CSV (max 20 MB).

────────────────────────────────────────

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
curl -X POST "http://localhost:8000/api/v1/ingest/?source=youtube"
curl -X POST "http://localhost:8000/api/v1/ingest/?source=google_drive"
curl -X POST "http://localhost:8000/api/v1/ingest/?source=local_folder"
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

Set `allow_local_fallback=False` when you want hard failures instead of silent fallback to `help/chunks.json`.

## RAGService usage rules

```python
from app.services.rag_service import RAGService
rag = RAGService()
rag.ingest({"source": "...", "chunk_id": "...", "text": "...", "topic": "...", "tags": "..."})
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
