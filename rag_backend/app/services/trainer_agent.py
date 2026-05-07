import asyncio
import datetime
import hashlib
import json
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db import Base, SessionLocal, engine
from app.models.knowledge_base import (
    KnowledgeChunk,
    TrainerResponseMemory,
    TrainerSourceSnapshot,
)
from app.services.google_drive_knowledge import GoogleDriveKnowledgeService
from app.services.rag_service import RAGService


logger = logging.getLogger(__name__)


class TrainerSubAgent:
    """Trainer sub-agent powered by NVIDIA NIM (LM Studio as fallback)."""

    CORE_WEBSITE_SOURCES = [
        "https://energiesparkommissar.de/video/bauphysik-zirkus-bauphysik-experimente-energiesparen-ohne-schimmel",
        "https://www.buildair.eu/",
        "https://effizienztagung.de/vortragende/",
    ]
    SOURCE_REFRESH_MINUTES = 60
    GOOGLE_DRIVE_REFRESH_MINUTES = 30

    def __init__(self) -> None:
        self._db_available = True
        self._volatile_source_snapshots: Dict[str, Dict[str, Any]] = {}
        self._volatile_response_memory: Dict[str, Dict[str, Any]] = {}
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create Trainer persistence tables if they do not exist yet."""
        try:
            Base.metadata.create_all(
                bind=engine,
                tables=[TrainerSourceSnapshot.__table__, TrainerResponseMemory.__table__],
            )
        except SQLAlchemyError:
            self._db_available = False

    @staticmethod
    def _normalize_question(question: str) -> str:
        return re.sub(r"\s+", " ", question.strip().lower())

    def _question_key(self, question: str) -> str:
        normalized = self._normalize_question(question)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _auth_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        api_key = settings.NVIDIA_API_KEY or settings.LLM_API_KEY
        if api_key and api_key.strip():
            headers["Authorization"] = f"Bearer {api_key.strip()}"
        return headers

    async def _post_chat_completion(
        self,
        client: httpx.AsyncClient,
        url: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Post a completion request, retrying once without auth if the endpoint returns 401."""
        headers = self._auth_headers()
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code == 401 and "Authorization" in headers:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        response.raise_for_status()
        return response.json()

    def _tool_specs(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_training_data",
                    "description": "Search local onboarding training chunks from the RAG knowledge base.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_google_drive_knowledge",
                    "description": "Search the primary Google Drive knowledge base snapshots.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_core_web_knowledge",
                    "description": "Search Trainer core website knowledge snapshots.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "recall_previous_training_response",
                    "description": "Retrieve a previously stored Trainer answer for a similar question.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                        },
                        "required": ["question"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_website_source",
                    "description": "Fetch and summarize a website source relevant to training.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "max_chars": {"type": "integer", "minimum": 500, "maximum": 12000},
                        },
                        "required": ["url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_youtube_channel_feed",
                    "description": "Read latest videos from a YouTube channel feed URL or channel ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel": {"type": "string"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                        },
                        "required": ["channel"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_vector_knowledge",
                    "description": (
                        "Semantic vector search over the EUZ Project knowledge base (ChromaDB). "
                        "Use this for questions about EUZ documents, seminars, evaluations, and training materials."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

    def _search_google_drive_knowledge(self, query: str, limit: int = 5) -> Dict[str, Any]:
        if not self._db_available:
            pattern = query.lower().strip()
            rows = []
            for snap in self._volatile_source_snapshots.values():
                if snap.get("source_type") != "google_drive":
                    continue
                searchable = (
                    f"{snap.get('title', '')} "
                    f"{snap.get('content', '')} "
                    f"{snap.get('source_url', '')}"
                ).lower()
                if pattern in searchable:
                    rows.append(snap)
            rows = rows[: max(1, min(limit, 10))]
            return {
                "count": len(rows),
                "items": [
                    {
                        "source_url": row.get("source_url"),
                        "title": row.get("title"),
                        "fetched_at": row.get("fetched_at"),
                        "content_excerpt": (row.get("content", "") or "")[:1200],
                    }
                    for row in rows
                ],
            }

        session = SessionLocal()
        try:
            pattern = f"%{query}%"
            rows = (
                session.query(TrainerSourceSnapshot)
                .filter(TrainerSourceSnapshot.source_type == "google_drive")
                .filter(
                    or_(
                        TrainerSourceSnapshot.title.ilike(pattern),
                        TrainerSourceSnapshot.content.ilike(pattern),
                        TrainerSourceSnapshot.source_url.ilike(pattern),
                    )
                )
                .order_by(TrainerSourceSnapshot.fetched_at.desc())
                .limit(max(1, min(limit, 10)))
                .all()
            )
            return {
                "count": len(rows),
                "items": [
                    {
                        "source_url": row.source_url,
                        "title": row.title,
                        "fetched_at": row.fetched_at.isoformat() if row.fetched_at else None,
                        "content_excerpt": (row.content or "")[:1200],
                    }
                    for row in rows
                ],
            }
        finally:
            session.close()

    def _search_core_web_knowledge(self, query: str, limit: int = 5) -> Dict[str, Any]:
        if not self._db_available:
            pattern = query.lower().strip()
            rows = []
            for snap in self._volatile_source_snapshots.values():
                searchable = (
                    f"{snap.get('title', '')} "
                    f"{snap.get('content', '')} "
                    f"{snap.get('source_url', '')}"
                ).lower()
                if pattern in searchable:
                    rows.append(snap)
            rows = rows[: max(1, min(limit, 10))]
            return {
                "count": len(rows),
                "items": [
                    {
                        "source_url": row.get("source_url"),
                        "title": row.get("title"),
                        "fetched_at": row.get("fetched_at"),
                        "content_excerpt": (row.get("content", "") or "")[:1200],
                    }
                    for row in rows
                ],
            }

        session = SessionLocal()
        try:
            pattern = f"%{query}%"
            rows = (
                session.query(TrainerSourceSnapshot)
                .filter(
                    or_(
                        TrainerSourceSnapshot.title.ilike(pattern),
                        TrainerSourceSnapshot.content.ilike(pattern),
                        TrainerSourceSnapshot.source_url.ilike(pattern),
                    )
                )
                .order_by(TrainerSourceSnapshot.fetched_at.desc())
                .limit(max(1, min(limit, 10)))
                .all()
            )
            return {
                "count": len(rows),
                "items": [
                    {
                        "source_url": row.source_url,
                        "title": row.title,
                        "fetched_at": row.fetched_at.isoformat() if row.fetched_at else None,
                        "content_excerpt": (row.content or "")[:1200],
                    }
                    for row in rows
                ],
            }
        finally:
            session.close()

    def _recall_previous_training_response(self, question: str) -> Dict[str, Any]:
        if not self._db_available:
            row = self._volatile_response_memory.get(self._question_key(question))
            if not row:
                return {"found": False}
            return {
                "found": True,
                "question": row.get("question"),
                "answer": row.get("answer"),
                "updated_at": row.get("updated_at"),
            }

        session = SessionLocal()
        try:
            key = self._question_key(question)
            row = (
                session.query(TrainerResponseMemory)
                .filter_by(question_key=key)
                .first()
            )
            if not row:
                return {"found": False}
            return {
                "found": True,
                "question": row.question,
                "answer": row.answer,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
        finally:
            session.close()

    def _search_vector_knowledge(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Semantic similarity search over ChromaDB using NVIDIA NIM embeddings."""
        try:
            rag = RAGService()
            results = rag.retrieve(query, top_k=min(limit, 10))
            return {
                "count": len(results),
                "items": [
                    {
                        "content": r["content"],
                        "source": r["metadata"].get("source", ""),
                        "score": round(r["score"], 4),
                    }
                    for r in results
                ],
            }
        except Exception as exc:
            logger.warning("Vector knowledge search failed: %s", exc)
            return {"count": 0, "items": [], "error": str(exc)}

    def _search_training_data(self, query: str, limit: int = 5) -> Dict[str, Any]:
        if not self._db_available:
            return {
                "count": 0,
                "items": [],
                "note": "Database unavailable; local training-data query is disabled.",
            }

        session = SessionLocal()
        try:
            pattern = f"%{query}%"
            rows = (
                session.query(KnowledgeChunk)
                .filter(
                    or_(
                        KnowledgeChunk.title.ilike(pattern),
                        KnowledgeChunk.topic.ilike(pattern),
                        KnowledgeChunk.content.ilike(pattern),
                        KnowledgeChunk.tags.ilike(pattern),
                    )
                )
                .order_by(KnowledgeChunk.updated_at.desc())
                .limit(max(1, min(limit, 10)))
                .all()
            )
            return {
                "count": len(rows),
                "items": [
                    {
                        "chunk_id": row.chunk_id,
                        "title": row.title,
                        "topic": row.topic,
                        "content": (row.content or "")[:1200],
                        "tags": row.tags,
                    }
                    for row in rows
                ],
            }
        finally:
            session.close()

    async def _read_website_source(self, url: str, max_chars: int = 4000) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

        text = response.text
        text = re.sub(r"<script[\\s\\S]*?</script>", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"<style[\\s\\S]*?</style>", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\\s+", " ", text).strip()
        return {
            "url": url,
            "excerpt": text[: max(500, min(max_chars, 12000))],
        }

    async def _refresh_core_sources(self) -> Dict[str, Any]:
        """Refresh core websites if snapshots are stale; keep latest snapshots persisted."""
        if not self._db_available:
            now = datetime.datetime.utcnow()
            stale_before = now - datetime.timedelta(minutes=self.SOURCE_REFRESH_MINUTES)
            refreshed = 0
            skipped = 0
            errors: List[Dict[str, str]] = []

            for url in self.CORE_WEBSITE_SOURCES:
                existing = self._volatile_source_snapshots.get(url)
                fetched_at = None
                if existing and existing.get("fetched_at"):
                    try:
                        fetched_at = datetime.datetime.fromisoformat(existing["fetched_at"])
                    except ValueError:
                        fetched_at = None

                if fetched_at and fetched_at > stale_before:
                    skipped += 1
                    continue

                try:
                    fetched = await self._read_website_source(url, max_chars=24000)
                    content = fetched.get("excerpt", "")
                    title = url
                    if content:
                        first_sentence = content.split(".")[0].strip()
                        if first_sentence:
                            title = first_sentence[:200]

                    self._volatile_source_snapshots[url] = {
                        "source_url": url,
                        "source_type": "website",
                        "title": title,
                        "content": content,
                        "content_hash": self._content_hash(content),
                        "fetched_at": now.isoformat(),
                    }
                    refreshed += 1
                except Exception as exc:
                    errors.append({"url": url, "error": str(exc)})

            return {"refreshed": refreshed, "skipped": skipped, "errors": errors}

        session = SessionLocal()
        now = datetime.datetime.utcnow()
        stale_before = now - datetime.timedelta(minutes=self.SOURCE_REFRESH_MINUTES)
        refreshed = 0
        skipped = 0
        errors: List[Dict[str, str]] = []

        try:
            for url in self.CORE_WEBSITE_SOURCES:
                existing = (
                    session.query(TrainerSourceSnapshot)
                    .filter_by(source_url=url)
                    .first()
                )
                if existing and existing.fetched_at and existing.fetched_at > stale_before:
                    skipped += 1
                    continue

                try:
                    fetched = await self._read_website_source(url, max_chars=24000)
                    content = fetched.get("excerpt", "")
                    title = url
                    if content:
                        first_sentence = content.split(".")[0].strip()
                        if first_sentence:
                            title = first_sentence[:200]

                    if existing:
                        existing.source_type = "website"
                        existing.title = title
                        existing.content = content
                        existing.content_hash = self._content_hash(content)
                        existing.fetched_at = now
                    else:
                        session.add(
                            TrainerSourceSnapshot(
                                source_url=url,
                                source_type="website",
                                title=title,
                                content=content,
                                content_hash=self._content_hash(content),
                                fetched_at=now,
                            )
                        )
                    refreshed += 1
                except Exception as exc:
                    errors.append({"url": url, "error": str(exc)})

            session.commit()
            return {
                "refreshed": refreshed,
                "skipped": skipped,
                "errors": errors,
            }
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def _refresh_google_drive_sources(self) -> Dict[str, Any]:
        service = GoogleDriveKnowledgeService()
        if not service.configured:
            return {
                "enabled": False,
                "refreshed": 0,
                "skipped": 0,
                "errors": [
                    {
                        "source": "google_drive",
                        "error": "Google Drive not configured. Set GOOGLE_DRIVE_API_KEY or GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE.",
                    }
                ],
            }

        now = datetime.datetime.utcnow()
        stale_before = now - datetime.timedelta(minutes=self.GOOGLE_DRIVE_REFRESH_MINUTES)

        if self._db_available:
            session = SessionLocal()
            try:
                latest = (
                    session.query(TrainerSourceSnapshot)
                    .filter(TrainerSourceSnapshot.source_type == "google_drive")
                    .order_by(TrainerSourceSnapshot.fetched_at.desc())
                    .first()
                )
                if latest and latest.fetched_at and latest.fetched_at > stale_before:
                    return {"enabled": True, "refreshed": 0, "skipped": 1, "errors": []}
            finally:
                session.close()
        else:
            recent = False
            for snap in self._volatile_source_snapshots.values():
                if snap.get("source_type") != "google_drive":
                    continue
                raw_fetched = snap.get("fetched_at")
                if not raw_fetched:
                    continue
                try:
                    fetched_at = datetime.datetime.fromisoformat(str(raw_fetched))
                except ValueError:
                    continue
                if fetched_at > stale_before:
                    recent = True
                    break
            if recent:
                return {"enabled": True, "refreshed": 0, "skipped": 1, "errors": []}

        try:
            chunks, stats = service.fetch_chunks()
        except Exception as exc:
            return {
                "enabled": True,
                "refreshed": 0,
                "skipped": 0,
                "errors": [{"source": "google_drive", "error": str(exc)}],
            }

        by_file: Dict[str, Dict[str, Any]] = {}
        for chunk in chunks:
            source = str(chunk.get("source", ""))
            chunk_id = str(chunk.get("chunk_id", ""))
            file_id = chunk_id.split("-", 1)[0] if chunk_id else ""
            if source not in by_file:
                by_file[source] = {
                    "file_id": file_id,
                    "title": source.replace("gdrive:", "", 1),
                    "parts": [],
                }
            if chunk.get("text"):
                by_file[source]["parts"].append(str(chunk["text"]))

        if self._db_available:
            session = SessionLocal()
            refreshed = 0
            errors: List[Dict[str, str]] = []
            try:
                for source, payload in by_file.items():
                    content = "\n".join(payload["parts"])[:30000]
                    if not content.strip():
                        continue
                    file_id = payload.get("file_id", "")
                    source_url = (
                        f"https://drive.google.com/file/d/{file_id}/view"
                        if file_id
                        else f"google-drive://{service.folder_id}/{source}"
                    )
                    row = (
                        session.query(TrainerSourceSnapshot)
                        .filter_by(source_url=source_url)
                        .first()
                    )
                    if row:
                        row.source_type = "google_drive"
                        row.title = payload["title"]
                        row.content = content
                        row.content_hash = self._content_hash(content)
                        row.fetched_at = now
                    else:
                        session.add(
                            TrainerSourceSnapshot(
                                source_url=source_url,
                                source_type="google_drive",
                                title=payload["title"],
                                content=content,
                                content_hash=self._content_hash(content),
                                fetched_at=now,
                            )
                        )
                    refreshed += 1
                session.commit()
            except Exception as exc:
                session.rollback()
                errors.append({"source": "google_drive", "error": str(exc)})
            finally:
                session.close()

            return {
                "enabled": True,
                "refreshed": refreshed,
                "skipped": 0,
                "errors": errors,
                "stats": stats,
            }

        refreshed = 0
        for source, payload in by_file.items():
            content = "\n".join(payload["parts"])[:30000]
            if not content.strip():
                continue
            file_id = payload.get("file_id", "")
            source_url = (
                f"https://drive.google.com/file/d/{file_id}/view"
                if file_id
                else f"google-drive://{service.folder_id}/{source}"
            )
            self._volatile_source_snapshots[source_url] = {
                "source_url": source_url,
                "source_type": "google_drive",
                "title": payload["title"],
                "content": content,
                "content_hash": self._content_hash(content),
                "fetched_at": now.isoformat(),
            }
            refreshed += 1

        return {
            "enabled": True,
            "refreshed": refreshed,
            "skipped": 0,
            "errors": [],
            "stats": stats,
        }

    def _build_google_drive_source_digest(self, limit_chars_per_source: int = 3000) -> str:
        max_sources = max(1, settings.TRAINER_SOURCE_DIGEST_MAX_SOURCES)
        chars_per_source = max(400, settings.TRAINER_SOURCE_DIGEST_MAX_CHARS_PER_SOURCE)
        if not self._db_available:
            rows = [
                row
                for row in self._volatile_source_snapshots.values()
                if row.get("source_type") == "google_drive"
            ]
            if not rows:
                return "No Google Drive knowledge snapshots available yet."

            lines: List[str] = []
            for row in rows[:max_sources]:
                lines.append(f"Source: {row.get('source_url')}")
                lines.append(f"Fetched: {row.get('fetched_at', 'unknown')}")
                lines.append(f"Content: {(row.get('content', '') or '')[:chars_per_source]}")
                lines.append("---")
            return "\n".join(lines)

        session = SessionLocal()
        try:
            rows = (
                session.query(TrainerSourceSnapshot)
                .filter(TrainerSourceSnapshot.source_type == "google_drive")
                .order_by(TrainerSourceSnapshot.fetched_at.desc())
                .limit(max_sources)
                .all()
            )
            if not rows:
                return "No Google Drive knowledge snapshots available yet."

            lines: List[str] = []
            for row in rows:
                lines.append(f"Source: {row.source_url}")
                lines.append(f"Fetched: {row.fetched_at.isoformat() if row.fetched_at else 'unknown'}")
                lines.append(f"Content: {(row.content or '')[:chars_per_source]}")
                lines.append("---")
            return "\n".join(lines)
        finally:
            session.close()

    def _build_core_source_digest(self, limit_chars_per_source: int = 3000) -> str:
        max_sources = max(1, settings.TRAINER_SOURCE_DIGEST_MAX_SOURCES)
        chars_per_source = max(400, settings.TRAINER_SOURCE_DIGEST_MAX_CHARS_PER_SOURCE)
        if not self._db_available:
            if not self._volatile_source_snapshots:
                return "No core website snapshots available yet."

            lines: List[str] = []
            rows = list(self._volatile_source_snapshots.values())[:max_sources]
            for row in rows:
                lines.append(f"Source: {row.get('source_url')}")
                lines.append(f"Fetched: {row.get('fetched_at', 'unknown')}")
                lines.append(f"Content: {(row.get('content', '') or '')[:chars_per_source]}")
                lines.append("---")
            return "\n".join(lines)

        session = SessionLocal()
        try:
            rows = (
                session.query(TrainerSourceSnapshot)
                .order_by(TrainerSourceSnapshot.fetched_at.desc())
                .limit(max_sources)
                .all()
            )
            if not rows:
                return "No core website snapshots available yet."

            lines: List[str] = []
            for row in rows:
                lines.append(f"Source: {row.source_url}")
                lines.append(f"Fetched: {row.fetched_at.isoformat() if row.fetched_at else 'unknown'}")
                lines.append(f"Content: {(row.content or '')[:chars_per_source]}")
                lines.append("---")
            return "\n".join(lines)
        finally:
            session.close()

    async def _safe_refresh(
        self,
        label: str,
        enabled: bool,
        refresh_fn: Callable[[], Awaitable[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        if not enabled:
            return {"enabled": False, "refreshed": 0, "skipped": 1, "errors": []}

        timeout_seconds = max(1, settings.TRAINER_REFRESH_TIMEOUT_SECONDS)
        try:
            return await asyncio.wait_for(refresh_fn(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            logger.warning("Trainer %s refresh timed out after %ss", label, timeout_seconds)
            return {
                "enabled": True,
                "refreshed": 0,
                "skipped": 0,
                "errors": [{"source": label, "error": f"refresh timeout after {timeout_seconds}s"}],
            }
        except Exception as exc:
            logger.warning("Trainer %s refresh failed: %s", label, exc)
            return {
                "enabled": True,
                "refreshed": 0,
                "skipped": 0,
                "errors": [{"source": label, "error": str(exc)}],
            }

    def _store_response_memory(self, question: str, answer: str, source_digest: str) -> None:
        if not self._db_available:
            self._volatile_response_memory[self._question_key(question)] = {
                "question": question,
                "answer": answer,
                "source_digest": source_digest[:12000],
                "updated_at": datetime.datetime.now(datetime.UTC).isoformat(),
            }
            return

        key = self._question_key(question)
        now = datetime.datetime.now(datetime.UTC)
        session = SessionLocal()
        try:
            row = session.query(TrainerResponseMemory).filter_by(question_key=key).first()
            if row:
                row.question = question
                row.answer = answer
                row.source_digest = source_digest[:12000]
                row.updated_at = now
            else:
                session.add(
                    TrainerResponseMemory(
                        question=question,
                        question_key=key,
                        answer=answer,
                        source_digest=source_digest[:12000],
                        created_at=now,
                        updated_at=now,
                    )
                )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def _read_youtube_channel_feed(self, channel: str, limit: int = 5) -> Dict[str, Any]:
        channel = channel.strip()
        if channel.startswith("https://www.youtube.com/feeds/videos.xml"):
            feed_url = channel
        elif channel.startswith("UC"):
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"
        else:
            match = re.search(r"/channel/([A-Za-z0-9_-]+)", channel)
            if not match:
                return {
                    "error": (
                        "Unsupported channel format. Use a YouTube feed URL or channel ID "
                        "starting with UC..."
                    )
                }
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={match.group(1)}"

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(feed_url)
            response.raise_for_status()

        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = []
        for entry in root.findall("atom:entry", ns)[: max(1, min(limit, 10))]:
            title_el = entry.find("atom:title", ns)
            link_el = entry.find("atom:link", ns)
            pub_el = entry.find("atom:published", ns)
            entries.append(
                {
                    "title": title_el.text if title_el is not None else "",
                    "url": link_el.attrib.get("href", "") if link_el is not None else "",
                    "published": pub_el.text if pub_el is not None else "",
                }
            )

        return {"feed_url": feed_url, "videos": entries}

    async def _run_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "search_training_data":
            return self._search_training_data(
                query=str(arguments.get("query", "")),
                limit=int(arguments.get("limit", 5)),
            )
        if name == "search_google_drive_knowledge":
            return self._search_google_drive_knowledge(
                query=str(arguments.get("query", "")),
                limit=int(arguments.get("limit", 5)),
            )
        if name == "search_core_web_knowledge":
            return self._search_core_web_knowledge(
                query=str(arguments.get("query", "")),
                limit=int(arguments.get("limit", 5)),
            )
        if name == "recall_previous_training_response":
            return self._recall_previous_training_response(
                question=str(arguments.get("question", ""))
            )
        if name == "read_website_source":
            return await self._read_website_source(
                url=str(arguments.get("url", "")),
                max_chars=int(arguments.get("max_chars", 4000)),
            )
        if name == "read_youtube_channel_feed":
            return await self._read_youtube_channel_feed(
                channel=str(arguments.get("channel", "")),
                limit=int(arguments.get("limit", 5)),
            )
        if name == "search_vector_knowledge":
            return self._search_vector_knowledge(
                query=str(arguments.get("query", "")),
                limit=int(arguments.get("limit", 5)),
            )
        return {"error": f"Unknown tool: {name}"}

    @staticmethod
    def _message_content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text" and item.get("text"):
                        parts.append(item["text"])
                    elif item.get("content"):
                        parts.append(str(item["content"]))
                else:
                    parts.append(str(item))
            return "\n".join(parts).strip()
        return str(content)

    @staticmethod
    def _compact_text(text: str, max_chars: int = 420) -> str:
        cleaned = re.sub(r"\s+", " ", (text or "").strip())
        if len(cleaned) <= max_chars:
            return cleaned
        return cleaned[: max_chars - 3].rstrip() + "..."

    async def _answer_via_lmstudio(
        self,
        messages: List[Dict[str, Any]],
        question: str,
        source_digest: str,
    ) -> str:
        """Run the trainer answer pipeline against LM Studio (NVIDIA NIM fallback)."""
        url = f"{settings.LM_STUDIO_BASE_URL}/v1/chat/completions"
        lm_headers = {"Content-Type": "application/json"}

        local_messages = list(messages)
        payload: Dict[str, Any] = {
            "model": settings.LM_STUDIO_MODEL,
            "messages": local_messages,
            "tools": self._tool_specs(),
            "tool_choice": "auto",
            "temperature": 1.0,
            "top_p": 0.95,
            "max_tokens": 700,
        }

        async with httpx.AsyncClient(timeout=75.0) as client:
            first_resp = await client.post(url, json=payload, headers=lm_headers)
            if first_resp.status_code == 400:
                # Model does not support tool-calling; retry without tools.
                no_tools_payload = {
                    k: v for k, v in payload.items() if k not in ("tools", "tool_choice")
                }
                first_resp = await client.post(
                    url, json=no_tools_payload, headers=lm_headers
                )
            first_resp.raise_for_status()
            first_data = first_resp.json()

        first_message = first_data["choices"][0]["message"]
        tool_calls = first_message.get("tool_calls") or []

        local_messages.append(
            {
                "role": "assistant",
                "content": first_message.get("content", ""),
                "tool_calls": tool_calls,
            }
        )

        if not tool_calls:
            return self._message_content_to_text(first_message.get("content", ""))

        for call in tool_calls:
            function_info = call.get("function", {})
            name = function_info.get("name", "")
            raw_args = function_info.get("arguments", "{}")
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except json.JSONDecodeError:
                args = {}
            tool_result = await self._run_tool(name, args or {})
            local_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id", ""),
                    "name": name,
                    "content": json.dumps(tool_result),
                }
            )

        second_payload = {
            "model": settings.LM_STUDIO_MODEL,
            "messages": local_messages,
            "temperature": 1.0,
            "top_p": 0.95,
            "max_tokens": 700,
        }
        async with httpx.AsyncClient(timeout=75.0) as client:
            second_resp = await client.post(
                url, json=second_payload, headers=lm_headers
            )
            second_resp.raise_for_status()
            second_data = second_resp.json()

        final_message = second_data["choices"][0]["message"]
        return self._message_content_to_text(final_message.get("content", ""))

    def _build_offline_fallback_answer(self, question: str) -> str:
        google_drive_hits = self._search_google_drive_knowledge(question, limit=3)
        training_hits = self._search_training_data(question, limit=3)
        core_hits = self._search_core_web_knowledge(question, limit=2)

        evidence_lines: List[str] = []

        for item in google_drive_hits.get("items", [])[:3]:
            title = item.get("title") or item.get("source_url") or "Google Drive source"
            snippet = self._compact_text(item.get("content_excerpt", ""))
            if snippet:
                evidence_lines.append(f"- Google Drive ({title}): {snippet}")

        for item in training_hits.get("items", [])[:2]:
            title = item.get("title") or item.get("topic") or item.get("chunk_id") or "Training data"
            snippet = self._compact_text(item.get("content", ""))
            if snippet:
                evidence_lines.append(f"- Training data ({title}): {snippet}")

        for item in core_hits.get("items", [])[:2]:
            title = item.get("title") or item.get("source_url") or "Website source"
            snippet = self._compact_text(item.get("content_excerpt", ""))
            if snippet:
                evidence_lines.append(f"- Website snapshot ({title}): {snippet}")

        if not evidence_lines:
            return (
                "NVIDIA NIM and LM Studio are both unavailable, and no indexed Trainer knowledge "
                "matched your question yet. "
                "Try rephrasing with specific keywords or ingesting/updating knowledge sources, then retry."
            )

        intro = (
            "NVIDIA NIM and LM Studio are both unavailable, so this answer was generated "
            "from indexed Trainer knowledge only. "
            "Please verify critical details before acting."
        )
        response = (
            f"{intro}\n\n"
            f"Question: {question}\n\n"
            "Most relevant evidence:\n"
            + "\n".join(evidence_lines)
        )
        return response

    async def answer(
        self,
        question: str,
        history: Optional[List[str]] = None,
        system_prompt_override: Optional[str] = None,
    ) -> str:
        drive_refresh = await self._safe_refresh(
            "google_drive",
            settings.TRAINER_AUTO_REFRESH_GOOGLE_DRIVE,
            self._refresh_google_drive_sources,
        )
        web_refresh = await self._safe_refresh(
            "core_web",
            settings.TRAINER_AUTO_REFRESH_CORE_WEB,
            self._refresh_core_sources,
        )
        source_digest = self._build_google_drive_source_digest()
        if source_digest.startswith("No Google Drive knowledge snapshots"):
            source_digest = self._build_core_source_digest()
        prior = self._recall_previous_training_response(question)
        if prior.get("found"):
            return (
                "Reused stored training response from memory:\n\n"
                f"{prior.get('answer', '')}"
            )

        system = (
            system_prompt_override
            or (
                "You are Trainer, a sub-agent focused on employee training. "
                "The EUZ Project document library is the primary and only knowledge base. "
                "Always start by calling search_vector_knowledge to retrieve relevant passages. "
                "Fall back to search_training_data for keyword-based lookup. "
                "Use core website snapshots only when EUZ documents do not cover the topic. "
                "Base all answers strictly on retrieved context."
            )
        )

        user_prompt = (
            f"{question}\n\n"
            "Primary Google Drive knowledge base (backend snapshots):\n"
            + source_digest
            + "\n\n"
            f"Google Drive refresh stats: {json.dumps(drive_refresh)}\n"
            f"Core websites refresh stats: {json.dumps(web_refresh)}"
        )

        messages: List[Dict[str, Any]] = [{"role": "system", "content": system}]
        for item in history or []:
            messages.append({"role": "user", "content": item})
        messages.append({"role": "user", "content": user_prompt})

        url = f"{settings.NVIDIA_BASE_URL.rstrip('/')}/chat/completions"
        payload: Dict[str, Any] = {
            "model": settings.NVIDIA_CHAT_MODEL,
            "messages": messages,
            "tools": self._tool_specs(),
            "tool_choice": "auto",
            "temperature": 1.0,
            "top_p": 0.95,
            "max_tokens": 700,
        }

        # Snapshot clean messages before any mutation so Ollama fallback
        # always starts from the original prompt.
        messages_for_fallback = list(messages)

        try:
            async with httpx.AsyncClient(timeout=75.0) as client:
                first_data = await self._post_chat_completion(client, url, payload)

            first_message = first_data["choices"][0]["message"]
            tool_calls = first_message.get("tool_calls") or []

            messages.append(
                {
                    "role": "assistant",
                    "content": first_message.get("content", ""),
                    "tool_calls": tool_calls,
                }
            )

            if not tool_calls:
                answer_text = self._message_content_to_text(first_message.get("content", ""))
                self._store_response_memory(question, answer_text, source_digest)
                return answer_text

            for call in tool_calls:
                function_info = call.get("function", {})
                name = function_info.get("name", "")
                raw_args = function_info.get("arguments", "{}")
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    args = {}

                tool_result = await self._run_tool(name, args or {})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id", ""),
                        "name": name,
                        "content": json.dumps(tool_result),
                    }
                )

            second_payload = {
                "model": settings.NVIDIA_CHAT_MODEL,
                "messages": messages,
                "temperature": 1.0,
                "top_p": 0.95,
                "max_tokens": 700,
            }

            async with httpx.AsyncClient(timeout=75.0) as client:
                second_data = await self._post_chat_completion(
                    client, url, second_payload
                )

            final_message = second_data["choices"][0]["message"]
            answer_text = self._message_content_to_text(final_message.get("content", ""))
            self._store_response_memory(question, answer_text, source_digest)
            return answer_text

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 400:
                # NVIDIA NIM model may not support tool-calling; retry without tools.
                fallback_payload = {
                    "model": settings.NVIDIA_CHAT_MODEL,
                    "messages": messages,
                    "temperature": 1.0,
                    "top_p": 0.95,
                    "max_tokens": 700,
                }
                try:
                    async with httpx.AsyncClient(timeout=75.0) as client:
                        fallback_data = await self._post_chat_completion(
                            client,
                            url,
                            fallback_payload,
                        )
                    fallback_message = fallback_data["choices"][0]["message"]
                    answer_text = self._message_content_to_text(
                        fallback_message.get("content", "")
                    )
                    self._store_response_memory(question, answer_text, source_digest)
                    return answer_text
                except Exception:
                    try:
                        answer_text = await self._answer_via_lmstudio(
                            messages_for_fallback, question, source_digest
                        )
                        self._store_response_memory(question, answer_text, source_digest)
                        return answer_text
                    except Exception:
                        return (
                            "NVIDIA NIM rejected the tool-calling request and LM Studio "
                            "fallback was also unavailable. Check NVIDIA_CHAT_MODEL and "
                            "that your NIM container supports function-calling."
                        )
            if exc.response.status_code == 401:
                try:
                    answer_text = await self._answer_via_lmstudio(
                        messages_for_fallback, question, source_digest
                    )
                    self._store_response_memory(question, answer_text, source_digest)
                    return answer_text
                except Exception:
                    return (
                        "NVIDIA NIM returned 401 Unauthorized and LM Studio fallback was "
                        "unavailable. Check NVIDIA_API_KEY in rag_backend/.env."
                    )
            return (
                f"Trainer agent request failed with status {exc.response.status_code}. "
                "Check NVIDIA_CHAT_MODEL and NIM container status."
            )
        except (httpx.ConnectError, httpx.ConnectTimeout, OSError):
            # NVIDIA NIM unreachable — fall back to LM Studio.
            try:
                answer_text = await self._answer_via_lmstudio(
                    messages_for_fallback, question, source_digest
                )
                self._store_response_memory(question, answer_text, source_digest)
                return answer_text
            except Exception:
                answer_text = self._build_offline_fallback_answer(question)
                self._store_response_memory(question, answer_text, source_digest)
                return answer_text
