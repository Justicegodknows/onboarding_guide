from fastapi import APIRouter
from app.models.schemas import DocumentUploadRequest, DocumentUploadResponse

router = APIRouter(prefix="/api/v1/documents")

@router.post("/upload")
def upload_document(request: DocumentUploadRequest):
    # Placeholder logic
    return DocumentUploadResponse(document_id="mock_id")
