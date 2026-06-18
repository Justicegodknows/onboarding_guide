from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.core.permissions import require_super_admin
from app.core.security import get_password_hash
from app.models.db_models import AuthUser

router = APIRouter(prefix="/platform", tags=["Platform (Super Admin)"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CreateTenantAdminRequest(BaseModel):
    tenant_id:        str = Field(min_length=2, description="Unique tenant identifier, e.g. company_abc")
    admin_email:      str
    admin_password:   str = Field(min_length=8)
    admin_department: str = Field(default="IT")
    display_name:     str = Field(default="")


# ---------------------------------------------------------------------------
# POST /platform/tenants
# Create a new tenant and its first Tenant Admin account.
# Only justicegsamuel@gmail.com (Super Admin) can call this.
# ---------------------------------------------------------------------------
@router.post("/tenants", status_code=status.HTTP_201_CREATED)
def create_tenant_and_admin(
    payload: CreateTenantAdminRequest,
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    normalized_email = payload.admin_email.lower().strip()
    if "@" not in normalized_email:
        raise HTTPException(status_code=400, detail="A valid admin_email is required")

    existing = db.query(AuthUser).filter(AuthUser.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Admin user already exists")

    admin_user = AuthUser(
        email=normalized_email,
        password_hash=get_password_hash(payload.admin_password),
        role="TENANT_ADMIN",
        dept=payload.admin_department,
        tenant_id=payload.tenant_id,
        display_name=payload.display_name or normalized_email,
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    return {
        "tenant_id": payload.tenant_id,
        "tenant_admin": {
            "email":      admin_user.email,
            "role":       admin_user.role,
            "department": admin_user.dept,
            "tenant_id":  admin_user.tenant_id,
        },
    }


# ---------------------------------------------------------------------------
# GET /platform/tenants
# List all distinct tenant_ids inferred from AuthUser rows.
# ---------------------------------------------------------------------------
@router.get("/tenants")
def list_tenants(
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(AuthUser.tenant_id).distinct().all()
    tenant_ids = sorted([r[0] for r in rows if r[0]])
    return {"tenants": tenant_ids}


# ---------------------------------------------------------------------------
# PATCH /platform/tenants/{tenant_id}/suspend
# Suspend all users in a tenant by setting their role to SUSPENDED.
# ---------------------------------------------------------------------------
@router.patch("/tenants/{tenant_id}/suspend")
def suspend_tenant(
    tenant_id: str,
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    users = db.query(AuthUser).filter(AuthUser.tenant_id == tenant_id).all()
    if not users:
        raise HTTPException(status_code=404, detail=f"No users found for tenant '{tenant_id}'")

    for u in users:
        u.role = "SUSPENDED"
    db.commit()

    return {"suspended": tenant_id, "affected_users": len(users)}


# ---------------------------------------------------------------------------
# GET /platform/usage
# Returns per-tenant user counts. Extend with token/request metrics later.
# ---------------------------------------------------------------------------
@router.get("/usage")
def platform_usage(
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(AuthUser.tenant_id).all()
    counts: dict[str, int] = {}
    for (tid,) in rows:
        key = tid or "__no_tenant__"
        counts[key] = counts.get(key, 0) + 1

    return {
        "usage": [{"tenant_id": k, "user_count": v} for k, v in sorted(counts.items())]
    }
