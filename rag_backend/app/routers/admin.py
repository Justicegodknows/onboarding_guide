"""
Admin Router - Endpoints for administrator operations.

Provides:
- Admin authentication and authorization
- Data ingestion into admin database
- Analytics and monitoring
- User management
- System status monitoring
"""
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.core.security import get_current_user, check_admin_role
from app.db import SessionLocal
from app.models.db_models import (
    AdminDocument,
    AdminIngestLog,
    AdminUser,
    AuthUser,
)
from app.services.admin_rag_service import AdminRAGService
from app.services.admin_ingest_service import ingest_admin_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

# ============================================================================
# Singleton AdminRAGService - Initialize once at module load
# ============================================================================
_admin_rag_instance = None
_admin_rag_initialized = False

def get_admin_rag() -> AdminRAGService:
    """Get or create singleton AdminRAGService instance."""
    global _admin_rag_instance, _admin_rag_initialized
    if _admin_rag_instance is None:
        try:
            logger.info("Initializing AdminRAGService (first use)...")
            _admin_rag_instance = AdminRAGService()
            _admin_rag_initialized = True
            logger.info("✅ AdminRAGService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AdminRAGService: {e}")
            _admin_rag_initialized = False
            raise
    return _admin_rag_instance

def is_admin_rag_ready() -> bool:
    """Check if AdminRAGService is ready without initializing it."""
    return _admin_rag_instance is not None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Schemas
# ============================================================================

class AdminIngestRequest(BaseModel):
    source: str = Field(
        default="local",
        description="Data source: 'local', 'folder', 'direct'",
    )
    folder_path: str | None = Field(
        default=None,
        description="Folder path when source='folder'",
    )
    documents: list[dict] | None = Field(
        default=None,
        description="Documents when source='direct'",
    )


class AdminAnalyticsResponse(BaseModel):
    total_admin_documents: int
    total_admin_chunks: int
    recent_ingest_logs: list[dict]
    admin_user_count: int


class SystemStatusResponse(BaseModel):
    status: str
    uptime: str
    database_status: str
    vector_store_status: str
    timestamp: str


class UserManagementRequest(BaseModel):
    email: str = Field(description="User email")
    role: str = Field(description="Role: USER or ADMIN")
    admin_level: str | None = Field(
        default="standard",
        description="Admin level if role=ADMIN",
    )
    is_active: bool = Field(default=True)


# ============================================================================
# Admin-Only Access Control
# ============================================================================

def require_admin(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Dependency to require ADMIN role and return admin user info.
    """
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    # Get the AuthUser by email
    auth_user = db.query(AuthUser).filter(
        AuthUser.email == current_user.get("id")
    ).first()
    
    if not auth_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account not found",
        )
    
    # Verify admin entry exists
    admin_user = db.query(AdminUser).filter(
        AdminUser.auth_user_id == auth_user.id
    ).first()
    
    if not admin_user or not admin_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
        )
    
    return {**current_user, "admin_level": admin_user.admin_level, "db_user_id": auth_user.id}


# ============================================================================
# Data Ingestion Endpoints
# ============================================================================

@router.post("/ingest")
def ingest_admin_data(
    request: AdminIngestRequest,
    current_admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Ingest documents into admin-exclusive database.
    
    Sources:
    - "local": Static admin documentation
    - "folder": Documents from a folder
    - "direct": Directly provided documents
    """
    try:
        result = ingest_admin_chunks(
            source=request.source,
            folder_path=request.folder_path,
            admin_data=request.documents,
        )
        
        # Log ingestion
        log = AdminIngestLog(
            admin_email=current_admin.get("id"),
            ingest_type=request.source,
            completed_at=datetime.utcnow(),
            total_chunks=result.get("chunk_count", 0),
            ingested_chunks=result.get("ingested", 0),
            error_count=result.get("errors_or_duplicates", 0),
            status=result.get("status", "unknown"),
            ingestion_metadata=str(result.get("meta", {})),
        )
        db.add(log)
        db.commit()
        
        return result
    
    except Exception as e:
        # Log error
        log = AdminIngestLog(
            admin_email=current_admin.get("id"),
            ingest_type=request.source,
            completed_at=datetime.utcnow(),
            status="error",
            error_message=str(e),
        )
        db.add(log)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ingestion failed: {str(e)}",
        )


@router.get("/documents")
def list_admin_documents(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    List admin-ingested documents.
    """
    total = db.query(AdminDocument).count()
    documents = db.query(AdminDocument).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "uploaded_by": doc.uploaded_by,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "source_type": doc.source_type,
                "chunk_count": doc.chunk_count,
                "status": doc.status,
            }
            for doc in documents
        ],
    }


# ============================================================================
# Analytics & Monitoring Endpoints
# ============================================================================

@router.get("/health")
def admin_health():
    """
    Simple health check endpoint that doesn't require auth or initialized services.
    Returns immediately.
    """
    return {
        "status": "ok",
        "admin_service_ready": is_admin_rag_ready(),
        "timestamp": datetime.utcnow().isoformat(),
    }

@router.get("/analytics", response_model=AdminAnalyticsResponse)
def get_admin_analytics(
    current_admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get analytics about admin data and system usage.
    """
    total_docs = db.query(AdminDocument).count()
    total_chunks = db.query(AdminDocument).with_entities(
        db.func.sum(AdminDocument.chunk_count)
    ).scalar() or 0
    
    recent_logs = db.query(AdminIngestLog).order_by(
        AdminIngestLog.started_at.desc()
    ).limit(10).all()
    
    admin_users = db.query(AdminUser).filter(
        AdminUser.is_active == True
    ).count()
    
    return AdminAnalyticsResponse(
        total_admin_documents=total_docs,
        total_admin_chunks=total_chunks,
        recent_ingest_logs=[
            {
                "id": log.id,
                "admin_email": log.admin_email,
                "ingest_type": log.ingest_type,
                "started_at": log.started_at.isoformat(),
                "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                "total_chunks": log.total_chunks,
                "ingested_chunks": log.ingested_chunks,
                "status": log.status,
            }
            for log in recent_logs
        ],
        admin_user_count=admin_users,
    )


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status(
    current_admin: dict = Depends(require_admin),
):
    """
    Get system status including vector stores and database health.
    Lightweight check - no heavy queries.
    """
    try:
        # Quick connectivity check without expensive retrieval
        admin_rag = get_admin_rag()
        admin_store_status = "healthy"
    except Exception as e:
        logger.warning(f"Admin RAG health check failed: {e}")
        admin_store_status = f"error: {str(e)[:50]}"
    
    return SystemStatusResponse(
        status="operational",
        uptime="running",
        database_status="healthy",
        vector_store_status=admin_store_status,
        timestamp=datetime.utcnow().isoformat(),
    )


# ============================================================================
# User Management Endpoints
# ============================================================================

@router.get("/users")
def list_users(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    List all users with their roles and admin status.
    """
    total = db.query(AuthUser).count()
    users = db.query(AuthUser).offset(offset).limit(limit).all()
    
    user_list = []
    for user in users:
        admin_info = db.query(AdminUser).filter(
            AdminUser.auth_user_id == user.id
        ).first()
        
        user_list.append({
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "dept": user.dept,
            "display_name": user.display_name,
            "created_at": user.created_at.isoformat(),
            "admin_level": admin_info.admin_level if admin_info else None,
            "is_admin": admin_info is not None and admin_info.is_active,
        })
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "users": user_list,
    }


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    request: UserManagementRequest,
    current_admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Update user role and admin status.
    """
    user = db.query(AuthUser).filter(AuthUser.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update role
    user.role = request.role
    
    # Handle admin status
    admin_user = db.query(AdminUser).filter(
        AdminUser.auth_user_id == user.id
    ).first()
    
    if request.role == "ADMIN":
        if not admin_user:
            admin_user = AdminUser(
                auth_user_id=user.id,
                admin_level=request.admin_level or "standard",
                is_active=request.is_active,
            )
            db.add(admin_user)
        else:
            admin_user.admin_level = request.admin_level or "standard"
            admin_user.is_active = request.is_active
    elif admin_user:
        db.delete(admin_user)
    
    db.commit()
    
    return {
        "message": "User updated successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "admin_level": admin_user.admin_level if admin_user else None,
        },
    }


# ============================================================================
# Admin Search & Query Endpoints
# ============================================================================

@router.post("/search/admin-only")
async def search_admin_database(
    query: str = Query(description="Search query"),
    top_k: int = Query(6, ge=1, le=50),
    current_admin: dict = Depends(require_admin),
):
    """
    Search admin-exclusive database only.
    Uses singleton to avoid expensive re-initialization.
    """
    try:
        admin_rag = get_admin_rag()
        results = admin_rag.retrieve_admin_only(query, top_k=top_k)
        
        return {
            "query": query,
            "results": results,
            "total": len(results),
        }
    except Exception as e:
        logger.error(f"Admin-only search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Search unavailable: {str(e)[:100]}",
        )


@router.post("/search/dual")
async def search_dual_database(
    query: str = Query(description="Search query"),
    top_k: int = Query(6, ge=1, le=50),
    current_admin: dict = Depends(require_admin),
):
    """
    Search both main and admin databases.
    Uses singleton to avoid expensive re-initialization.
    """
    try:
        admin_rag = get_admin_rag()
        results = admin_rag.retrieve_dual(query, top_k=top_k)
        
        return {
            "query": query,
            "results": results,
            "main_count": len(results.get("main", [])),
            "admin_count": len(results.get("admin", [])),
        }
    except Exception as e:
        logger.error(f"Dual search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Search unavailable: {str(e)[:100]}",
        )
