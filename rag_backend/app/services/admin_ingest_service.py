"""
Admin Ingestion Service - Dedicated pipeline for admin data ingestion.

Handles chunking, indexing, and tracking of admin-specific documents
in the exclusive admin database.
"""
import os
import json
from typing import Any, Dict, List, Tuple

from app.services.admin_rag_service import AdminRAGService


def ingest_admin_chunks(
    source: str = "local",
    folder_path: str | None = None,
    admin_data: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Ingest documents into admin-exclusive database.
    
    Supports multiple sources:
    - "local": Static admin documentation
    - "folder": Local folder with admin documents
    - "direct": Direct admin data (dicts)
    
    Args:
        source: Ingestion source type
        folder_path: Path to folder (when source="folder")
        admin_data: List of admin documents as dicts (when source="direct")
        
    Returns:
        Ingestion result with status, counts, and metadata
    """
    admin_rag = AdminRAGService()
    
    ingest_source = (source or "").strip().lower()
    if ingest_source not in {"local", "folder", "direct"}:
        raise ValueError(
            "source must be one of: 'local', 'folder', 'direct'."
        )
    
    meta: Dict[str, Any] = {}
    chunks: List[Dict[str, Any]] = []
    
    if ingest_source == "local":
        # Load from static admin help documentation
        help_dir = os.path.join(os.path.dirname(__file__), '../../../help')
        admin_chunks_path = os.path.join(help_dir, 'admin_chunks.json')
        
        if os.path.exists(admin_chunks_path):
            with open(admin_chunks_path, 'r') as f:
                chunks = json.load(f)
            meta = {"source": "local", "chunk_count": len(chunks)}
        else:
            # Return empty if no admin chunks file exists
            return {
                "status": "warning",
                "ingest_source": "local",
                "chunk_count": 0,
                "ingested": 0,
                "errors_or_duplicates": 0,
                "meta": {"message": "No admin_chunks.json found"},
            }
    
    elif ingest_source == "folder":
        if not folder_path:
            raise ValueError("folder_path required when source='folder'")
        
        chunks = _load_folder_documents(folder_path)
        meta = {"source": "folder", "folder_path": folder_path, "chunk_count": len(chunks)}
    
    elif ingest_source == "direct":
        if not admin_data:
            raise ValueError("admin_data required when source='direct'")
        
        chunks = admin_data
        meta = {"source": "direct", "chunk_count": len(chunks)}
    
    # Ingest chunks into admin database
    success = 0
    errors = 0
    for chunk in chunks:
        result = admin_rag.ingest_admin(chunk)
        if result.get("status") == "success":
            success += 1
        else:
            errors += 1
    
    result = {
        "status": "success",
        "ingest_source": meta.get("source", ingest_source),
        "chunk_count": len(chunks),
        "ingested": success,
        "errors_or_duplicates": errors,
        "meta": meta,
    }
    
    print(
        f"Admin Ingestion completed via {result['ingest_source']}: "
        f"{success} ingested, {errors} errors/duplicates, {len(chunks)} chunks seen."
    )
    return result


def _load_folder_documents(folder_path: str) -> List[Dict[str, Any]]:
    """
    Load documents from a folder.
    
    Supports: .json, .txt, .md, .pdf (if PyMuPDF available)
    
    Args:
        folder_path: Path to folder containing documents
        
    Returns:
        List of document chunks
    """
    import importlib
    
    chunks = []
    
    if not os.path.isdir(folder_path):
        raise ValueError(f"Folder not found: {folder_path}")
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if not os.path.isfile(file_path):
            continue
        
        try:
            if filename.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        chunks.extend(data)
                    else:
                        chunks.append(data)
            
            elif filename.endswith(('.txt', '.md')):
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    chunks.append({
                        "text": content,
                        "source": filename,
                        "type": "text"
                    })
            
            elif filename.endswith('.pdf'):
                try:
                    fitz = importlib.import_module("fitz")
                    with fitz.open(file_path) as doc:
                        text = ""
                        for page in doc:
                            text += page.get_text()
                    chunks.append({
                        "text": text,
                        "source": filename,
                        "type": "pdf"
                    })
                except ImportError:
                    print(f"Skipping PDF {filename}: PyMuPDF not available")
        
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    return chunks
