---
name: rag-retrieval
description: Retrieve grounded evidence from the VaultMind ChromaDB knowledge base before answering. Use when the user asks a factual, document-specific, policy, or domain question — anything that should be answered from the corpus rather than general knowledge. Also use when debugging retrieval quality or deciding which documents are relevant. Triggers on any question referencing "the docs", "our data", "the handbook", "the knowledge base", domain-specific lookups, or phrases like "look up", "find in the documents", "retrieve", "search the knowledge base", "what does the document say about".
---

You retrieve evidence before you answer. No factual claim leaves your mouth without a retrieved chunk behind it.

## System architecture (know before you query)

- **Vector store**: ChromaDB, persisted at `./chroma_db`
- **Embedding model**: `NvidiaEmbeddings` via `RAGService` in `rag_backend/app/services/rag_service.py`
  - Passage embedding (`input_type: "passage"`) — used at ingest time
  - Query embedding (`input_type: "query"`) — used at retrieval time
  - Model: `NVIDIA_EMBED_MODEL` from `.env` (currently `nvidia/llama-nemotron-embed-1b-v2`)
- **CRITICAL**: The embedding model at query time MUST match the model used during ingestion. Never change `NVIDIA_EMBED_MODEL` without re-ingesting all documents.
- **LangChain interface**: `RAGService.retrieve(query, top_k, filter_metadata)` returns a list of `{content, metadata, score}` dicts.

---

## Retrieval workflow

### 1. Reformulate the query — never search with the raw user question

Generate 2–4 query variants before calling `retrieve()`:

| Variant | How to form it |
|---|---|
| **Literal** | The user's question, lightly cleaned (remove filler words, keep entities) |
| **Keyword-only** | Nouns, named entities, policy terms, dates — no verbs or connectives |
| **Decomposed** | Break multi-part questions into one sub-question per concern |
| **HyDE** | Write a short sentence that a correct answer might literally contain |

The NVIDIA asymmetric embedding model (`llama-nemotron-embed-1b-v2`) performs best with short declarative phrases, not full questions — prefer the keyword and HyDE variants.

---

### 2. Retrieve broadly, then narrow

```python
from app.services.rag_service import RAGService
rag = RAGService()

# Run each query variant; collect all results
results = rag.retrieve(query=query_variant, top_k=8)
```

- Use `top_k=8–10` per variant for broad or multi-part questions; `top_k=3–5` for narrow lookups.
- **Deduplicate** across variants by `chunk_id` — keep the highest-scoring copy of each.
- **Re-rank** the deduplicated set by: semantic score → recency (`published` metadata) → source authority (Drive/YouTube/local).
- **Drop weak hits**: discard any chunk with score below ~0.3. Do not pad context with low-relevance results to appear thorough.
- Use `filter_metadata` only with confirmed keys (e.g. `{"source": "youtube:UCxxxxxx"}`). Never guess metadata values.

---

### 3. Multi-hop when needed

If the first retrieval is insufficient (partial or no coverage):

1. Extract key entities and terms from the chunks you did retrieve.
2. Issue a second retrieval using those terms as new queries.
3. Stop after 2–3 hops — further hops rarely help and increase latency.

---

### 4. Coverage check (before answering)

Ask: *Do the retrieved chunks actually answer the question?*

| Coverage | Action |
|---|---|
| **Full** — chunks directly answer the question | Answer with citations |
| **Partial** — some but not all parts are covered | Answer the supported portion, explicitly flag the gap → hand off to `uncertainty-protocol` |
| **None** — all chunks are irrelevant or all scores < 0.3 | Do not answer from general knowledge → hand off to `uncertainty-protocol` |
| **Contradictory** — chunks conflict | Prefer the chunk with the more recent `published` date; if unclear, present both and flag → hand off to `uncertainty-protocol` |

---

## Known knowledge sources

Chunks in ChromaDB originate from these ingestion paths (see `ingest_chunks.py`):

| Source tag | Origin | Notes |
|---|---|---|
| `youtube:UC...` | `@e.u.z-am-deister` YouTube channel | Transcripts in German/English; fallback to metadata if no transcript |
| `google_drive` | Google Drive folder `1vN7M2R14vNXCKvU2Y0ouCWeVZnuTEjAP` | PDFs, DOCX, XLSX, TXT |
| `local` | `help/chunks.json` | Static fallback chunks |
| `local_folder` | `rag_backend/docs/EUZ Project/` | On-disk EUZ project documents |

Use the `tags` and `topic` metadata fields from returned chunks to understand which domain area a chunk belongs to.

---

## Citation rules (summary — see `citation-discipline` skill for full detail)

- Every factual sentence cites at least one chunk: `[Filename.pdf, p.14]` or `[Video: "Title", youtube:UC...]`.
- Never invent a source. If you can't cite it, you can't claim it.
- Quoting verbatim: use quotes and cite. Paraphrasing: still cite.
- End every cited answer with a `**Sources**` list matching all inline citations.

---

## Debugging retrieval quality

1. Read `chroma_db/chroma.sqlite3` metadata to verify what is indexed.
2. Compare retrieved chunk text with the final LLM answer — any claim not traceable to a chunk is hallucinated.
3. Do **not** modify binary files in `chroma_db/`. Always interact via `RAGService`.
4. If retrieval is poor for a known document, the likely causes are:
   - Document not ingested — check `chunk_count` in the last ingestion response
   - Embedding model changed after ingestion — re-ingest required
   - Chunk size (`YOUTUBE_CHUNK_SIZE`, `GOOGLE_DRIVE_CHUNK_SIZE`) is too large or too small
   - Query variant didn't match the indexed text — try the HyDE or keyword variant

---

## Forbidden

- Answering factual questions without retrieval.
- Passing the user's raw message directly as the query — always reformulate.
- Stuffing low-relevance chunks (score < 0.3) into context to look thorough.
- Returning chunks to the user verbatim — synthesize and cite.
- Inventing document names, section numbers, dates, or URLs.
- Using `filter_metadata` with guessed keys — only confirmed metadata fields.
- Mixing retrieved facts with general knowledge without labeling which is which.
- Bypassing `RAGService` to access ChromaDB directly.
