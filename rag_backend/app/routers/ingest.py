from fastapi import APIRouter, Query
from app.services.ingest_chunks import ingest_chunks

router = APIRouter(prefix="/api/v1/ingest")

@router.post("/")
def trigger_ingestion(
    source: str = Query(
        default="google_drive",
        pattern="^(google_drive|local)$",
        description="Knowledge source for ingestion.",
    ),
    allow_local_fallback: bool = Query(
        default=True,
        description="Fallback to local help/chunks.json when Google Drive is unavailable.",
    ),
):
    # Run the ingestion and capture output
    try:
        result = ingest_chunks(source=source, allow_local_fallback=allow_local_fallback)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}
