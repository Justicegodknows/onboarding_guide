from fastapi import APIRouter, Query
from app.services.ingest_chunks import ingest_chunks

router = APIRouter(prefix="/api/v1/ingest")

@router.post("/")
def trigger_ingestion(
    source: str = Query(
        default="google_drive",
        pattern="^(google_drive|youtube|local|local_folder)$",
        description=(
            "Knowledge source for ingestion. "
            "'google_drive' — Google Drive folder; "
            "'youtube' — YouTube channel transcripts; "
            "'local' — static help/chunks.json; "
            "'local_folder' — EUZ Project docs folder on disk (DGX Spark)."
        ),
    ),
    youtube_channel: str | None = Query(
        default=None,
        description="YouTube channel reference (handle URL, channel URL, feed URL, or channel ID).",
    ),
    folder_path: str | None = Query(
        default=None,
        description=(
            "Absolute path to a local documents folder. Only used when source='local_folder'. "
            "Overrides the EUZ_DOCS_FOLDER environment variable for this request."
        ),
    ),
    allow_local_fallback: bool = Query(
        default=True,
        description="Fallback to local help/chunks.json when Google Drive or YouTube is unavailable.",
    ),
):
    # Run the ingestion and capture output
    try:
        result = ingest_chunks(
            source=source,
            allow_local_fallback=allow_local_fallback,
            youtube_channel=youtube_channel,
            folder_path=folder_path,
        )
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}
