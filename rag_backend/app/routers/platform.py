# rag_backend/app/routers/platform.py
# Level 1 -- Super Admin endpoints (role=SUPER_ADMIN only)
# POST   /platform/tenants              create a new tenant
# GET    /platform/tenants              list all tenants
# PATCH  /platform/tenants/{tenant_id} suspend/activate/change plan
# GET    /platform/usage               cross-tenant usage stats

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.permissions import require_super_admin
from app.db import SessionLocal
from app.models.db_models import AuthUser, Tenant

router = APIRouter(prefix="/platform", tags=["Platform (Super Admin)"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CreateTenantRequest(BaseModel):
    tenant_id: str = Field(description="Unique slug, e.g. company_abc")
    name: str = Field(description="Human-readable company name")
    plan: str = Field(default="starter", description="starter | pro | enterprise")
    admin_email: str = Field(description="Email of the first Tenant Admin")


class UpdateTenantRequest(BaseModel):
    status: Optional[str] = Field(None, description="active | suspended")
    plan: Optional[str] = Field(None)
    name: Optional[str] = Field(None)


@router.post("/tenants", status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: CreateTenantRequest,
    db: Session = Depends(get_db),
    _sa: dict = Depends(require_super_admin),
):
    """
    Create a new tenant and provision its first Tenant Admin account.
    The Tenant Admin gets a random password -- they must reset it via the invite flow.
    """
    existing = db.query(Tenant).filter(Tenant.tenant_id == payload.tenant_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Tenant '{payload.tenant_id}' already exists.")

    tenant = Tenant(
        tenant_id=payload.tenant_id,
        name=payload.name,
        plan=payload.plan,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(tenant)
    db.flush()

    admin_user = db.query(AuthUser).filter(
        AuthUser.email == payload.admin_email.lower().strip()
    ).first()

    if not admin_user:
        import secrets
        from app.core.security import get_password_hash
        admin_user = AuthUser(
            email=payload.admin_email.lower().strip(),
            password_hash=get_password_hash(secrets.token_urlsafe(32)),
            role="TENANT_ADMIN",
            dept="IT",
            tenant_id=payload.tenant_id,
            display_name=payload.admin_email,
        )
        db.add(admin_user)
    else:
        admin_user.role = "TENANT_ADMIN"
        admin_user.tenant_id = payload.tenant_id

    db.commit()
    db.refresh(tenant)

    return {
        "message": "Tenant created successfully.",
        "tenant_id": tenant.tenant_id,
        "name": tenant.name,
        "plan": tenant.plan,
        "status": tenant.status,
        "admin_email": payload.admin_email,
    }


@router.get("/tenants")
def list_tenants(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _sa: dict = Depends(require_super_admin),
):
    """List all tenants on the platform with user counts."""
    total = db.query(Tenant).count()
    tenants = db.query(Tenant).offset(offset).limit(limit).all()
    return {
        "total": total,
        "tenants": [
            {
                "tenant_id": t.tenant_id,
                "name": t.name,
                "plan": t.plan,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "user_count": db.query(AuthUser).filter(AuthUser.tenant_id == t.tenant_id).count(),
            }
            for t in tenants
        ],
    }


@router.patch("/tenants/{tenant_id}")
def update_tenant(
    tenant_id: str,
    payload: UpdateTenantRequest,
    db: Session = Depends(get_db),
    _sa: dict = Depends(require_super_admin),
):
    """
    Suspend or activate a tenant, or change their billing plan.
    Suspending sets status=suspended -- data is preserved, logins are blocked.
    """
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    if payload.status is not None:
        if payload.status not in ("active", "suspended"):
            raise HTTPException(status_code=400, detail="status must be 'active' or 'suspended'.")
        tenant.status = payload.status
    if payload.plan is not None:
        tenant.plan = payload.plan
    if payload.name is not None:
        tenant.name = payload.name

    tenant.updated_at = datetime.utcnow()
    db.commit()

    return {
        "message": f"Tenant '{tenant_id}' updated.",
        "tenant_id": tenant.tenant_id,
        "status": tenant.status,
        "plan": tenant.plan,
        "name": tenant.name,
    }


@router.get("/usage")
def platform_usage(
    db: Session = Depends(get_db),
    _sa: dict = Depends(require_super_admin),
):
    """
    Cross-tenant usage overview for billing and monitoring.
    Returns per-tenant user counts and plan breakdown.
    """
    tenants = db.query(Tenant).all()
    rows = []
    for t in tenants:
        user_count = db.query(AuthUser).filter(AuthUser.tenant_id == t.tenant_id).count()
        rows.append({
            "tenant_id": t.tenant_id,
            "name": t.name,
            "plan": t.plan,
            "status": t.status,
            "user_count": user_count,
        })
    return {
        "total_tenants": len(rows),
        "active_tenants": sum(1 for r in rows if r["status"] == "active"),
        "suspended_tenants": sum(1 for r in rows if r["status"] == "suspended"),
        "total_users": sum(r["user_count"] for r in rows),
        "tenants": rows,
    }
