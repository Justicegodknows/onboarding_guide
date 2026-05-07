import os
import uuid
import shutil
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import SessionLocal
from app.models.db_models import Document
from app.services.rag_service import RAGService

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../../uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv"}
MAX_FILE_SIZE_MB = 50

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a document (PDF, DOCX, TXT, MD, CSV), store it, chunk it, and embed it into ChromaDB."""
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{ext}' is not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {MAX_FILE_SIZE_MB} MB limit.",
        )

    # Persist to uploads directory with a unique name to prevent collisions
    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(dest_path, "wb") as f:
        f.write(content)

    # Track in database
    db_doc = Document(
        filename=file.filename,
        uploaded_by=int(current_user["id"]) if str(current_user.get("id", "")).isdigit() else None,
        uploaded_at=date.today(),
        document_metadata=f'{{"doc_id": "{doc_id}", "original_name": "{file.filename}", "size_bytes": {len(content)}}}',
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Trigger chunking + embedding via RAGService
    try:
        rag = RAGService()
        result = rag.ingest(dest_path, metadata={"doc_id": doc_id, "filename": file.filename, "source": "upload"})
        ingest_status = result.get("status", "unknown")
        chunks_added = result.get("chunks_added", 0)
    except Exception as exc:
        ingest_status = "error"
        chunks_added = 0
        # Don't roll back the file — the document is stored; re-ingest can be triggered later
        print(f"[documents] Ingestion failed for {file.filename}: {exc}")

    return {
        "document_id": doc_id,
        "db_id": db_doc.id,
        "filename": file.filename,
        "size_bytes": len(content),
        "ingest_status": ingest_status,
        "chunks_added": chunks_added,
    }


@router.get("/", response_model=List[dict])
def list_documents(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all uploaded documents."""
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "uploaded_by": d.uploaded_by,
            "uploaded_at": str(d.uploaded_at) if d.uploaded_at else None,
            "metadata": d.document_metadata,
        }
        for d in docs
    ]


@router.delete("/{doc_id}", status_code=status.HTTP_200_OK)
def delete_document(
    doc_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a document record. Admin only."""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    db.delete(doc)
    db.commit()
    return {"message": f"Document {doc_id} deleted."}


@router.post("/{doc_id}/reingest", status_code=status.HTTP_200_OK)
def reingest_document(
    doc_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-trigger chunking and embedding for an existing uploaded document."""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    import json
    try:
        meta = json.loads(doc.document_metadata or "{}")
    except Exception:
        meta = {}

    raw_doc_id = meta.get("doc_id", "")
    # Try to find the file by matching prefix
    matched_file = None
    for fname in os.listdir(UPLOAD_DIR):
        if fname.startswith(raw_doc_id):
            matched_file = os.path.join(UPLOAD_DIR, fname)
            break

    if not matched_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found on disk.")

    rag = RAGService()
    result = rag.ingest(matched_file, metadata={"doc_id": raw_doc_id, "filename": doc.filename, "source": "upload"})
    return {"message": "Re-ingestion triggered.", **result}

