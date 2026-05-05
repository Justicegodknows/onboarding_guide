from fastapi import APIRouter, Query
from app.services.ingest_chunks import ingest_chunks

router = APIRouter(prefix="/api/v1/ingest")

@router.post("/")
def trigger_ingestion(
    source: str = Query(
        default="google_drive",
        pattern="^(google_drive|youtube|local)$",
        description="Knowledge source for ingestion.",
    ),
    youtube_channel: str | None = Query(
        default=None,
        description="YouTube channel reference (handle URL, channel URL, feed URL, or channel ID).",
    ),
    allow_local_fallback: bool = Query(
        default=True,
        description="Fallback to local help/chunks.json when Google Drive is unavailable.",
    ),
):
    # Run the ingestion and capture output
    try:
        result = ingest_chunks(
            source=source,
            allow_local_fallback=allow_local_fallback,
            youtube_channel=youtube_channel,
        )
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}
