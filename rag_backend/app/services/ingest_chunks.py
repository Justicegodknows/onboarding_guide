import os
import json
from typing import Any, Dict, List, Tuple

import httpx

from app.services.rag_service import RAGService
from app.services.google_drive_knowledge import GoogleDriveKnowledgeService
from app.services.youtube_knowledge import YouTubeKnowledgeService

HELP_DIR = os.path.join(os.path.dirname(__file__), '../../../help')
CHUNKS_PATH = os.path.join(HELP_DIR, 'chunks.json')



def _load_local_chunks() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    with open(CHUNKS_PATH, 'r') as f:
        chunks = json.load(f)
    return chunks, {"source": "local", "chunk_count": len(chunks)}


def _load_google_drive_chunks() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    service = GoogleDriveKnowledgeService()
    if not service.configured:
        raise RuntimeError(
            "Google Drive source is not configured. Set GOOGLE_DRIVE_API_KEY and "
            "GOOGLE_DRIVE_FOLDER_ID/GOOGLE_DRIVE_FOLDER_URL."
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


def ingest_chunks(
    source: str = "google_drive",
    allow_local_fallback: bool = True,
    youtube_channel: str | None = None,
):
    rag = RAGService()

    ingest_source = (source or "").strip().lower()
    if ingest_source not in {"google_drive", "youtube", "local"}:
        raise ValueError("source must be one of 'google_drive', 'youtube', or 'local'.")

    meta: Dict[str, Any] = {}
    if ingest_source == "google_drive":
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

    success = 0
    errors = 0
    for chunk in chunks:
        result = rag.ingest(chunk)
        if result:
            success += 1
        else:
            errors += 1

    result = {
        "status": "success",
        "ingest_source": meta.get("source", ingest_source),
        "chunk_count": len(chunks),
        "ingested": success,
        "errors_or_duplicates": errors,
        "meta": meta,
    }
    print(
        f"Ingestion completed via {result['ingest_source']}: "
        f"{success} ingested, {errors} errors/duplicates, {len(chunks)} chunks seen."
    )
    return result

if __name__ == "__main__":
    ingest_chunks()
