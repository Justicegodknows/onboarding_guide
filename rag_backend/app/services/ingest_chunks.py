import datetime
import json
import logging
import os
from typing import Any, Dict, List, Tuple

import httpx

from app.db import SessionLocal
from app.models.knowledge_base import KnowledgeChunk
from app.services.google_drive_knowledge import GoogleDriveKnowledgeService
from app.services.local_folder_knowledge import LocalFolderKnowledgeService
from app.services.rag_service import RAGService
from app.services.youtube_knowledge import YouTubeKnowledgeService

logger = logging.getLogger(__name__)

HELP_DIR = os.path.join(os.path.dirname(__file__), "../../help")
CHUNKS_PATH = os.path.join(HELP_DIR, "chunks.json")


def _load_local_chunks() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    with open(CHUNKS_PATH, "r") as f:
        chunks = json.load(f)
    return chunks, {"source": "local", "chunk_count": len(chunks)}


def _load_google_drive_chunks() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    service = GoogleDriveKnowledgeService()
    if not service.configured:
        raise RuntimeError(
            "Google Drive source is not configured. Set GOOGLE_DRIVE_API_KEY or "
            "GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE, plus GOOGLE_DRIVE_FOLDER_ID."
        )
    chunks, stats = service.fetch_chunks()
    return chunks, {"source": "google_drive", **stats}


def _load_youtube_chunks(channel: str | None = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    service = YouTubeKnowledgeService(channel=channel)
    if not service.configured:
        raise RuntimeError(
            "YouTube source is not configured. Provide a channel URL/ID via query parameter "
            "or set YOUTUBE_CHANNEL in rag_backend/.env."
        )
    chunks, stats = service.fetch_chunks()
    return chunks, {"source": "youtube", **stats}


def _load_local_folder_chunks() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    service = LocalFolderKnowledgeService()
    if not service.configured:
        raise RuntimeError(
            f"EUZ docs folder not found: {service.folder_path}. "
            "Set EUZ_DOCS_FOLDER in rag_backend/.env."
        )
    chunks, stats = service.fetch_chunks()
    return chunks, {"source": "local_folder", **stats}


def _upsert_knowledge_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, int]:
    """Write chunks to the KnowledgeChunk SQL table for trainer keyword search."""
    session = SessionLocal()
    inserted = 0
    updated = 0
    try:
        now = datetime.datetime.utcnow()
        for chunk in chunks:
            chunk_id = str(chunk.get("chunk_id", ""))
            content = str(chunk.get("text") or chunk.get("content") or "").strip()
            if not chunk_id or not content:
                continue

            row = session.query(KnowledgeChunk).filter_by(chunk_id=chunk_id).first()
            if row:
                row.content = content
                row.topic = chunk.get("topic", "")
                row.tags = chunk.get("tags", "")
                row.title = chunk.get("source", "")
                row.updated_at = now
                updated += 1
            else:
                session.add(
                    KnowledgeChunk(
                        chunk_id=chunk_id,
                        title=chunk.get("source", ""),
                        topic=chunk.get("topic", ""),
                        content=content,
                        tags=chunk.get("tags", ""),
                        created_at=now,
                        updated_at=now,
                    )
                )
                inserted += 1

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return {"inserted": inserted, "updated": updated}


def ingest_chunks(
    source: str = "local_folder",
    allow_local_fallback: bool = True,
    youtube_channel: str | None = None,
):
    rag = RAGService()

    ingest_source = (source or "").strip().lower()
    valid_sources = {"google_drive", "youtube", "local", "local_folder"}
    if ingest_source not in valid_sources:
        raise ValueError(f"source must be one of: {', '.join(sorted(valid_sources))}.")

    meta: Dict[str, Any] = {}

    if ingest_source == "local_folder":
        chunks, meta = _load_local_folder_chunks()
    elif ingest_source == "google_drive":
        try:
            chunks, meta = _load_google_drive_chunks()
        except (RuntimeError, httpx.HTTPError) as exc:
            if not allow_local_fallback:
                raise
            chunks, meta = _load_local_chunks()
            meta["fallback_reason"] = str(exc)
    elif ingest_source == "youtube":
        try:
            chunks, meta = _load_youtube_chunks(youtube_channel)
        except (RuntimeError, httpx.HTTPError) as exc:
            if not allow_local_fallback:
                raise
            chunks, meta = _load_local_chunks()
            meta["fallback_reason"] = str(exc)
    else:
        chunks, meta = _load_local_chunks()

    # --- Vector store (ChromaDB) ---
    vec_success = 0
    vec_errors = 0
    for chunk in chunks:
        result = rag.ingest(chunk)
        if result and result.get("status") == "success":
            vec_success += 1
        else:
            vec_errors += 1

    # --- SQL store (KnowledgeChunk) for trainer keyword search ---
    sql_stats: Dict[str, int] = {"inserted": 0, "updated": 0}
    try:
        sql_stats = _upsert_knowledge_chunks(chunks)
    except Exception as exc:
        logger.warning("KnowledgeChunk SQL upsert failed: %s", exc)

    result = {
        "status": "success",
        "ingest_source": meta.get("source", ingest_source),
        "chunk_count": len(chunks),
        "vector_store": {"ingested": vec_success, "errors": vec_errors},
        "sql_store": sql_stats,
        "meta": meta,
    }
    logger.info(
        "Ingestion via %s: %d chunks → vector(%d ok, %d err) sql(%d ins, %d upd)",
        result["ingest_source"],
        len(chunks),
        vec_success,
        vec_errors,
        sql_stats["inserted"],
        sql_stats["updated"],
    )
    return result


if __name__ == "__main__":
    ingest_chunks()
