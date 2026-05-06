import logging
import os
import re
import subprocess
import tempfile
from io import BytesIO
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx
from docx import Document
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pypdf import PdfReader

from app.core.config import settings
from app.services.chunk_documents import chunk_text

try:
    import pytesseract
    from PIL import Image as _PILImage
    _OCR_AVAILABLE = True
except ImportError:
    _OCR_AVAILABLE = False

try:
    import whisper as _whisper_mod
    _WHISPER_AVAILABLE = True
except ImportError:
    _WHISPER_AVAILABLE = False

logger = logging.getLogger(__name__)


DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
GOOGLE_DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class GoogleDriveKnowledgeService:
    """Fetch and chunk public Google Drive folder content for RAG ingestion."""

    WHISPER_MODEL_SIZE: str = "tiny"
    _whisper_model: Optional[Any] = None  # class-level lazy cache

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
        service_account_file: Optional[str] = None,
        folder_id: Optional[str] = None,
        folder_url: Optional[str] = None,
        chunk_size: Optional[int] = None,
        max_files: Optional[int] = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else settings.GOOGLE_DRIVE_API_KEY).strip()
        self.service_account_file = (
            service_account_file
            if service_account_file is not None
            else settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE
        ).strip()
        self.folder_id = self._resolve_folder_id(
            folder_id if folder_id is not None else settings.GOOGLE_DRIVE_FOLDER_ID,
            folder_url if folder_url is not None else settings.GOOGLE_DRIVE_FOLDER_URL,
        )
        self.chunk_size = chunk_size if chunk_size is not None else settings.GOOGLE_DRIVE_CHUNK_SIZE
        self.max_files = max_files if max_files is not None else settings.GOOGLE_DRIVE_MAX_FILES
        self._drive_service = self._build_drive_service() if self.service_account_file else None

    def _build_drive_service(self) -> Any:
        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_file,
            scopes=GOOGLE_DRIVE_SCOPES,
        )
        return build("drive", "v3", credentials=credentials, cache_discovery=False)

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
        return bool((self.api_key or self._drive_service is not None) and self.folder_id)

    def _request_json(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._drive_service is not None:
            if path != "/files":
                raise ValueError(f"Unsupported Google Drive JSON path: {path}")
            return self._drive_service.files().list(**params).execute()

        if not self.api_key:
            raise RuntimeError(
                "Google Drive credentials are missing. Set GOOGLE_DRIVE_API_KEY or "
                "GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE."
            )
        params = dict(params)
        params["key"] = self.api_key
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{DRIVE_API_BASE}{path}", params=params)
            response.raise_for_status()
            return response.json()

    def _request_bytes(self, path: str, params: Dict[str, Any]) -> bytes:
        if self._drive_service is not None:
            file_id = path.strip("/").split("/")[1]
            files_resource = self._drive_service.files()
            if path.endswith("/export"):
                request = files_resource.export_media(
                    fileId=file_id,
                    mimeType=params["mimeType"],
                )
            else:
                request = files_resource.get_media(
                    fileId=file_id,
                    supportsAllDrives=params.get("supportsAllDrives"),
                )
            return request.execute()

        if not self.api_key:
            raise RuntimeError(
                "Google Drive credentials are missing. Set GOOGLE_DRIVE_API_KEY or "
                "GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE."
            )
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
            "Note: OCR/transcription was unavailable or returned no text. Access the file directly via the link above."
        )
        return "\n".join(lines)

    @staticmethod
    def _extract_image_ocr(content: bytes) -> str:
        """Run Tesseract OCR on image bytes. Returns empty string if unavailable or unsuccessful."""
        if not _OCR_AVAILABLE:
            logger.debug("pytesseract/Pillow not installed; skipping OCR.")
            return ""
        try:
            image = _PILImage.open(BytesIO(content))
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as exc:
            logger.warning("OCR failed: %s", exc)
            return ""

    @classmethod
    def _get_whisper_model(cls) -> Any:
        """Lazy-load and cache the Whisper model at class level."""
        if not _WHISPER_AVAILABLE:
            raise RuntimeError("openai-whisper is not installed.")
        if cls._whisper_model is None:
            logger.info(
                "Loading Whisper model '%s' (may download ~%s on first run)…",
                cls.WHISPER_MODEL_SIZE,
                {"tiny": "72 MB", "base": "142 MB"}.get(cls.WHISPER_MODEL_SIZE, "?"),
            )
            cls._whisper_model = _whisper_mod.load_model(cls.WHISPER_MODEL_SIZE)
        return cls._whisper_model

    @classmethod
    def _transcribe_audio_bytes(cls, audio_bytes: bytes, suffix: str = ".wav") -> str:
        """Transcribe raw audio bytes with Whisper. Returns empty string on failure."""
        if not _WHISPER_AVAILABLE:
            logger.debug("openai-whisper not installed; skipping transcription.")
            return ""
        tmp_path = ""
        try:
            model = cls._get_whisper_model()
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            result = model.transcribe(tmp_path)
            return (result.get("text") or "").strip()
        except Exception as exc:
            logger.warning("Audio transcription failed: %s", exc)
            return ""
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @classmethod
    def _extract_video_transcription(cls, video_bytes: bytes, src_suffix: str = ".mp4") -> str:
        """Extract audio from video with ffmpeg, then transcribe with Whisper."""
        if not _WHISPER_AVAILABLE:
            logger.debug("openai-whisper not installed; skipping video transcription.")
            return ""
        video_path = ""
        audio_path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=src_suffix, delete=False) as vtmp:
                vtmp.write(video_bytes)
                video_path = vtmp.name
            audio_path = video_path + ".audio.wav"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", video_path,
                    "-vn", "-acodec", "pcm_s16le",
                    "-ar", "16000", "-ac", "1",
                    audio_path,
                ],
                capture_output=True,
                check=True,
            )
            with open(audio_path, "rb") as af:
                audio_bytes = af.read()
            return cls._transcribe_audio_bytes(audio_bytes, suffix=".wav")
        except subprocess.CalledProcessError as exc:
            logger.warning(
                "ffmpeg audio extraction failed: %s",
                exc.stderr.decode(errors="ignore"),
            )
            return ""
        except Exception as exc:
            logger.warning("Video transcription failed: %s", exc)
            return ""
        finally:
            for p in (video_path, audio_path):
                if p and os.path.exists(p):
                    os.unlink(p)

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

        if mime_type.startswith("image/"):
            content = self._request_bytes(
                f"/files/{file_id}",
                {"alt": "media", "supportsAllDrives": "true"},
            )
            ocr_text = self._extract_image_ocr(content)
            return ocr_text if ocr_text else self._build_media_metadata_text(file_meta)

        if mime_type.startswith("audio/"):
            content = self._request_bytes(
                f"/files/{file_id}",
                {"alt": "media", "supportsAllDrives": "true"},
            )
            ext = "." + mime_type.split("/")[-1].split(";")[0]
            transcript = self._transcribe_audio_bytes(content, suffix=ext)
            return transcript if transcript else self._build_media_metadata_text(file_meta)

        if mime_type.startswith("video/"):
            content = self._request_bytes(
                f"/files/{file_id}",
                {"alt": "media", "supportsAllDrives": "true"},
            )
            ext = "." + mime_type.split("/")[-1].split(";")[0]
            transcript = self._extract_video_transcription(content, src_suffix=ext)
            return transcript if transcript else self._build_media_metadata_text(file_meta)

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