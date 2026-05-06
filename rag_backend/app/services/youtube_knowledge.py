import re
import subprocess
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import settings
from app.services.chunk_documents import chunk_text

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:  # pragma: no cover - dependency may be optional at import time
    YouTubeTranscriptApi = None  # type: ignore[assignment]


ATOM_NS = "http://www.w3.org/2005/Atom"
MEDIA_NS = "http://search.yahoo.com/mrss/"
YOUTUBE_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class YouTubeKnowledgeService:
    """Fetch and chunk YouTube channel videos for RAG ingestion."""

    def __init__(
        self,
        *,
        channel: Optional[str] = None,
        max_videos: Optional[int] = None,
        chunk_size: Optional[int] = None,
    ) -> None:
        self.channel = (channel or settings.YOUTUBE_CHANNEL).strip()
        self.max_videos = max_videos if max_videos is not None else settings.YOUTUBE_MAX_VIDEOS
        self.chunk_size = chunk_size if chunk_size is not None else settings.YOUTUBE_CHUNK_SIZE

    @property
    def configured(self) -> bool:
        return bool(self.channel)

    @staticmethod
    def _extract_channel_id(channel: str) -> Optional[str]:
        value = (channel or "").strip()
        if not value:
            return None

        if re.fullmatch(r"UC[a-zA-Z0-9_-]{20,}", value):
            return value

        if "channel_id=" in value:
            match = re.search(r"channel_id=([A-Za-z0-9_-]+)", value)
            if match:
                return match.group(1)

        match = re.search(r"/channel/([A-Za-z0-9_-]+)", value)
        if match:
            return match.group(1)

        return None

    def _resolve_channel_id(self, channel: str) -> str:
        extracted = self._extract_channel_id(channel)
        if extracted:
            return extracted

        url = channel if channel.startswith("http") else f"https://www.youtube.com/{channel.lstrip('@')}"
        if "/@" not in url and "youtube.com/" in url and not re.search(r"/(channel|c|user)/", url):
            url = url.rstrip("/") + "/videos"

        with httpx.Client(
            timeout=25.0,
            follow_redirects=True,
            headers=YOUTUBE_HTTP_HEADERS,
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            html = response.text

        id_match = re.search(r"channel_id=(UC[A-Za-z0-9_-]{20,})", html)
        if id_match:
            return id_match.group(1)

        # Primary path: RSS link embeds channel_id.
        rss_match = re.search(r"https://www\.youtube\.com/feeds/videos\.xml\?channel_id=([A-Za-z0-9_-]+)", html)
        if rss_match:
            return rss_match.group(1)

        escaped_rss_match = re.search(
            r"https:\\/\\/www\\.youtube\\.com\\/feeds\\/videos\\.xml\\?channel_id=([A-Za-z0-9_-]+)",
            html,
        )
        if escaped_rss_match:
            return escaped_rss_match.group(1)

        # Fallback: canonical /channel/UC... URL.
        canonical_match = re.search(
            r"(?:https://www\\.youtube\\.com|/channel)/channel/([A-Za-z0-9_-]+)",
            html,
        )
        if canonical_match:
            return canonical_match.group(1)

        # Last resort: curl often bypasses consent pages better than HTTP clients.
        try:
            output = subprocess.check_output(["curl", "-sL", url], text=True)
            curl_match = re.search(r"channel_id=(UC[A-Za-z0-9_-]{20,})", output)
            if curl_match:
                return curl_match.group(1)
        except Exception:
            pass

        raise RuntimeError("Unable to resolve YouTube channel ID from the provided channel reference.")

    def _build_feed_url(self, channel: str) -> Tuple[str, str]:
        channel_id = self._resolve_channel_id(channel)
        return channel_id, f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    @staticmethod
    def _extract_video_id(entry: ET.Element, ns: Dict[str, str]) -> str:
        video_id = entry.findtext("yt:videoId", default="", namespaces=ns)
        if video_id:
            return video_id

        link_el = entry.find("atom:link", ns)
        href = link_el.attrib.get("href", "") if link_el is not None else ""
        match = re.search(r"[?&]v=([A-Za-z0-9_-]{6,})", href)
        return match.group(1) if match else ""

    @staticmethod
    def _fetch_transcript(video_id: str) -> str:
        if not video_id or YouTubeTranscriptApi is None:
            return ""

        try:
            # Backward-compatible call style.
            pieces = YouTubeTranscriptApi.get_transcript(video_id, languages=["de", "en"])  # type: ignore[attr-defined]
            return " ".join((piece.get("text") or "").strip() for piece in pieces if piece.get("text")).strip()
        except Exception:
            pass

        try:
            # Newer object-based API style.
            api = YouTubeTranscriptApi()  # type: ignore[operator]
            transcript = api.fetch(video_id, languages=["de", "en"])  # type: ignore[attr-defined]
            joined = " ".join((item.text or "").strip() for item in transcript if getattr(item, "text", "")).strip()
            return joined
        except Exception:
            return ""

    @staticmethod
    def _build_metadata_fallback(title: str, url: str, published: str, description: str) -> str:
        lines = [
            "YouTube video metadata.",
            f"Title: {title}",
            f"Published: {published}",
            f"URL: {url}",
        ]
        if description:
            lines.append(f"Description: {description}")
        lines.append("Note: Transcript was unavailable for this video.")
        return "\n".join(lines)

    def fetch_chunks(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not self.configured:
            raise RuntimeError("YouTube channel source is not configured.")

        channel_id, feed_url = self._build_feed_url(self.channel)
        with httpx.Client(
            timeout=25.0,
            follow_redirects=True,
            headers=YOUTUBE_HTTP_HEADERS,
        ) as client:
            response = client.get(feed_url)
            response.raise_for_status()
            feed_xml = response.text

        ns = {
            "atom": ATOM_NS,
            "media": MEDIA_NS,
            "yt": "http://www.youtube.com/xml/schemas/2015",
        }
        root = ET.fromstring(feed_xml)
        entries = root.findall("atom:entry", ns)[: max(1, self.max_videos)]

        chunks: List[Dict[str, Any]] = []
        failed_videos: List[Dict[str, str]] = []
        transcripted = 0

        for entry in entries:
            title = entry.findtext("atom:title", default="", namespaces=ns).strip()
            link_el = entry.find("atom:link", ns)
            video_url = link_el.attrib.get("href", "") if link_el is not None else ""
            published = entry.findtext("atom:published", default="", namespaces=ns).strip()
            description = entry.findtext("media:group/media:description", default="", namespaces=ns).strip()
            video_id = self._extract_video_id(entry, ns)
            if not video_id:
                failed_videos.append({"title": title or "unknown", "error": "Missing video ID"})
                continue

            transcript = self._fetch_transcript(video_id)
            if transcript:
                transcripted += 1
            text = transcript or self._build_metadata_fallback(title, video_url, published, description)

            envelope = (
                f"Video title: {title}\n"
                f"Video URL: {video_url}\n"
                f"Published: {published}\n\n"
                f"Content:\n{text}"
            )
            for idx, piece in enumerate(chunk_text(envelope, chunk_size=self.chunk_size)):
                if not piece.strip():
                    continue
                chunks.append(
                    {
                        "source": f"youtube:{channel_id}",
                        "chunk_id": f"{video_id}-{idx}",
                        "text": piece,
                        "topic": title or video_id,
                        "tags": "youtube,trainer",
                    }
                )

        stats = {
            "channel": self.channel,
            "channel_id": channel_id,
            "feed_url": feed_url,
            "videos_seen": len(entries),
            "videos_with_transcript": transcripted,
            "failed_videos": failed_videos,
            "chunk_count": len(chunks),
        }
        return chunks, stats