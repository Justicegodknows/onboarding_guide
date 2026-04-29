from fastapi import APIRouter
from app.services.ingest_chunks import ingest_chunks

router = APIRouter(prefix="/api/v1/ingest")

@router.post("/")
def trigger_ingestion():
    # Run the ingestion and capture output
    try:
        ingest_chunks()
        return {"status": "success", "message": "Ingestion completed."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
