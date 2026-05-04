import re
from io import BytesIO
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx
from docx import Document
from pypdf import PdfReader

from app.core.config import settings
from app.services.chunk_documents import chunk_text


DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"


class GoogleDriveKnowledgeService:
    """Fetch and chunk public Google Drive folder content for RAG ingestion."""

    EXPORT_MIME_MAP = {
        "application/vnd.google-apps.document": "text/plain",
        "application/vnd.google-apps.spreadsheet": "text/csv",
        "application/vnd.google-apps.presentation": "text/plain",
    }

    DIRECT_TEXT_MIME_PREFIXES = (
        "text/",
        "application/json",
        "application/xml",
    )
    DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    PDF_MIME = "application/pdf"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        folder_id: Optional[str] = None,
        folder_url: Optional[str] = None,
        chunk_size: Optional[int] = None,
        max_files: Optional[int] = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else settings.GOOGLE_DRIVE_API_KEY).strip()
        self.folder_id = self._resolve_folder_id(
            folder_id if folder_id is not None else settings.GOOGLE_DRIVE_FOLDER_ID,
            folder_url if folder_url is not None else settings.GOOGLE_DRIVE_FOLDER_URL,
        )
        self.chunk_size = chunk_size if chunk_size is not None else settings.GOOGLE_DRIVE_CHUNK_SIZE
        self.max_files = max_files if max_files is not None else settings.GOOGLE_DRIVE_MAX_FILES

    @staticmethod
    def _extract_folder_id(folder_ref: str) -> Optional[str]:
        value = (folder_ref or "").strip()
        if not value:
            return None

        match = re.search(r"/folders/([a-zA-Z0-9_-]+)", value)
        if match:
            return match.group(1)

        if re.fullmatch(r"[a-zA-Z0-9_-]{10,}", value):
            return value

        return None

    def _resolve_folder_id(self, folder_id: str, folder_url: str) -> Optional[str]:
        explicit = self._extract_folder_id(folder_id)
        if explicit:
            return explicit
        return self._extract_folder_id(folder_url)

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.folder_id)

    def _request_json(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("GOOGLE_DRIVE_API_KEY is missing.")
        params = dict(params)
        params["key"] = self.api_key
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{DRIVE_API_BASE}{path}", params=params)
            response.raise_for_status()
            return response.json()

    def _request_bytes(self, path: str, params: Dict[str, Any]) -> bytes:
        if not self.api_key:
            raise RuntimeError("GOOGLE_DRIVE_API_KEY is missing.")
        params = dict(params)
        params["key"] = self.api_key
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{DRIVE_API_BASE}{path}", params=params)
            response.raise_for_status()
            return response.content

    def _iter_folder_items(self, root_folder_id: str) -> Iterable[Tuple[Dict[str, Any], str]]:
        stack: List[str] = [root_folder_id]
        yielded = 0

        while stack and yielded < self.max_files:
            folder_id = stack.pop()
            page_token: Optional[str] = None
            while yielded < self.max_files:
                data = self._request_json(
                    "/files",
                    {
                        "q": f"'{folder_id}' in parents and trashed=false",
                        "fields": (
                            "nextPageToken,files("
                            "id,name,mimeType,modifiedTime,size,webViewLink,description"
                            ")"
                        ),
                        "pageSize": 100,
                        "supportsAllDrives": "true",
                        "includeItemsFromAllDrives": "true",
                        "pageToken": page_token,
                    },
                )
                files = data.get("files", [])
                for item in files:
                    mime = item.get("mimeType", "")
                    if mime == "application/vnd.google-apps.folder":
                        stack.append(item.get("id", ""))
                        continue
                    yielded += 1
                    yield item, folder_id
                    if yielded >= self.max_files:
                        break

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

    @staticmethod
    def _build_media_metadata_text(file_meta: Dict[str, Any]) -> str:
        filename = file_meta.get("name", "unknown")
        mime_type = file_meta.get("mimeType", "")
        web_link = file_meta.get("webViewLink", "")
        modified = file_meta.get("modifiedTime", "")
        size = file_meta.get("size", "")
        description = file_meta.get("description", "")

        lines = [
            "Media asset available in Google Drive.",
            f"File name: {filename}",
            f"MIME type: {mime_type}",
        ]
        if size:
            lines.append(f"File size (bytes): {size}")
        if modified:
            lines.append(f"Last modified: {modified}")
        if description:
            lines.append(f"Description: {description}")
        if web_link:
            lines.append(f"Open link: {web_link}")
        lines.append(
            "Note: This is binary media. Text transcript/OCR extraction is not enabled in this ingestion path yet."
        )
        return "\n".join(lines)

    @staticmethod
    def _extract_docx_text(content: bytes) -> str:
        doc = Document(BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        reader = PdfReader(BytesIO(content))
        parts: List[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                parts.append(page_text)
        return "\n".join(parts)

    def _download_file_text(self, file_meta: Dict[str, Any]) -> str:
        file_id = file_meta.get("id", "")
        mime_type = file_meta.get("mimeType", "")
        filename = str(file_meta.get("name", "")).lower()
        if not file_id:
            return ""

        if mime_type in self.EXPORT_MIME_MAP:
            exported = self._request_bytes(
                f"/files/{file_id}/export",
                {"mimeType": self.EXPORT_MIME_MAP[mime_type], "supportsAllDrives": "true"},
            )
            return exported.decode("utf-8", errors="ignore")

        if mime_type.startswith(self.DIRECT_TEXT_MIME_PREFIXES):
            content = self._request_bytes(
                f"/files/{file_id}",
                {"alt": "media", "supportsAllDrives": "true"},
            )
            return content.decode("utf-8", errors="ignore")

        if mime_type == self.PDF_MIME or filename.endswith(".pdf"):
            content = self._request_bytes(
                f"/files/{file_id}",
                {"alt": "media", "supportsAllDrives": "true"},
            )
            return self._extract_pdf_text(content)

        if mime_type == self.DOCX_MIME or filename.endswith(".docx"):
            content = self._request_bytes(
                f"/files/{file_id}",
                {"alt": "media", "supportsAllDrives": "true"},
            )
            return self._extract_docx_text(content)

        if mime_type.startswith("image/") or mime_type.startswith("video/") or mime_type.startswith("audio/"):
            return self._build_media_metadata_text(file_meta)

        return ""

    def fetch_chunks(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not self.folder_id:
            raise RuntimeError("Google Drive folder ID is missing.")

        chunks: List[Dict[str, Any]] = []
        processed_files = 0
        skipped_files = 0
        failed_files: List[Dict[str, str]] = []

        for file_meta, _ in self._iter_folder_items(self.folder_id):
            file_id = file_meta.get("id", "")
            filename = file_meta.get("name", "unknown")
            source_label = f"gdrive:{filename}"
            try:
                text = self._download_file_text(file_meta)
                if not text.strip():
                    skipped_files += 1
                    continue

                for idx, piece in enumerate(chunk_text(text, chunk_size=self.chunk_size)):
                    if not piece.strip():
                        continue

                    tags = ["google_drive"]
                    mime = str(file_meta.get("mimeType", ""))
                    if mime.startswith("image/"):
                        tags.append("image")
                    elif mime.startswith("video/"):
                        tags.append("video")
                    elif mime.startswith("audio/"):
                        tags.append("audio")
                    elif mime == self.PDF_MIME or filename.lower().endswith(".pdf"):
                        tags.append("pdf")
                    elif mime == self.DOCX_MIME or filename.lower().endswith(".docx"):
                        tags.append("docx")

                    chunks.append(
                        {
                            "source": source_label,
                            "chunk_id": f"{file_id}-{idx}",
                            "text": piece,
                            "topic": filename,
                            "tags": ",".join(tags),
                        }
                    )

                processed_files += 1
            except Exception as exc:
                failed_files.append({"file": filename, "error": str(exc)})

        stats = {
            "folder_id": self.folder_id,
            "processed_files": processed_files,
            "skipped_files": skipped_files,
            "failed_files": failed_files,
            "chunk_count": len(chunks),
        }
        return chunks, stats