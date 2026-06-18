from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.db_models import AuthUser
from app.core.permissions import require_tenant_admin, assert_same_tenant
from app.core.security import get_password_hash

router = APIRouter(prefix="/tenant", tags=["Tenant Admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CreateTenantUserRequest(BaseModel):
    email:        str
    password:     str = Field(min_length=8)
    department:   str = Field(default="General")
    display_name: str = Field(default="")
    role:         str = Field(default="USER", description="USER or TENANT_ADMIN")


# ---------------------------------------------------------------------------
# GET /tenant/users
# List all users in the caller's tenant.
# ---------------------------------------------------------------------------
@router.get("/users")
def list_users(
    current_user: dict = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
):
    tenant_id = current_user.get("tenant_id")
    users = (
        db.query(AuthUser)
        .filter(AuthUser.tenant_id == tenant_id)
        .order_by(AuthUser.email.asc())
        .all()
    )

    return [
        {
            "email":        u.email,
            "role":         u.role,
            "department":   u.dept,
            "tenant_id":    u.tenant_id,
            "display_name": u.display_name,
            "created_at":   u.created_at,
        }
        for u in users
    ]


# ---------------------------------------------------------------------------
# POST /tenant/users
# Create a new user inside the caller's tenant.
# ---------------------------------------------------------------------------
@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateTenantUserRequest,
    current_user: dict = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
):
    tenant_id = current_user.get("tenant_id")

    normalized_email = payload.email.lower().strip()
    if "@" not in normalized_email:
        raise HTTPException(status_code=400, detail="A valid email is required")

    existing = db.query(AuthUser).filter(AuthUser.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    role = (payload.role or "USER").strip().upper()
    if role not in ("USER", "TENANT_ADMIN"):
        raise HTTPException(status_code=400, detail="role must be USER or TENANT_ADMIN")

    user = AuthUser(
        email=normalized_email,
        password_hash=get_password_hash(payload.password),
        role=role,
        dept=payload.department,
        tenant_id=tenant_id,
        display_name=payload.display_name or normalized_email,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "email":        user.email,
        "role":         user.role,
        "department":   user.dept,
        "tenant_id":    user.tenant_id,
        "display_name": user.display_name,
    }


# ---------------------------------------------------------------------------
# DELETE /tenant/users/{email}
# Remove a user from the caller's tenant.
# ---------------------------------------------------------------------------
@router.delete("/users/{email}")
def delete_user(
    email: str,
    current_user: dict = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
):
    normalized_email = email.lower().strip()

    user = db.query(AuthUser).filter(AuthUser.email == normalized_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent cross-tenant deletion
    assert_same_tenant(current_user, user.tenant_id or "")

    # Prevent self-deletion
    if normalized_email == (current_user.get("id") or "").lower().strip():
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    db.delete(user)
    db.commit()
    return {"deleted": normalized_email}


# ---------------------------------------------------------------------------
# POST /tenant/documents/upload
# Upload a document into the tenant's scoped ChromaDB collection.
# Wire to your ingestion pipeline once tenant-scoped ingest is finalised.
# ---------------------------------------------------------------------------
@router.post("/documents/upload")
async def upload_document(
    current_user: dict = Depends(require_tenant_admin),
    file: UploadFile = File(...),
):
    return {
        "message":   "Upload received. Connect to your tenant-scoped ingestion pipeline.",
        "filename":  file.filename,
        "tenant_id": current_user.get("tenant_id"),
    }
