from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user


# ---------------------------------------------------------------------------
# Role constants
# ---------------------------------------------------------------------------
ROLE_SUPER_ADMIN  = "SUPER_ADMIN"
ROLE_TENANT_ADMIN = "TENANT_ADMIN"
ROLE_USER         = "USER"

# Platform-owner bootstrap: this email is always treated as Super Admin
# regardless of the role stored in the DB.
SUPER_ADMIN_EMAIL = "justicegsamuel@gmail.com"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_role(role: Optional[str]) -> str:
    return (role or "").strip().upper()


def _is_super_admin_identity(user: Dict[str, Any]) -> bool:
    """Return True if the token belongs to the platform owner."""
    email = (user.get("id") or "").strip().lower()
    role  = _normalize_role(user.get("role"))
    return role == ROLE_SUPER_ADMIN or email == SUPER_ADMIN_EMAIL.lower()


# ---------------------------------------------------------------------------
# FastAPI dependency guards
# ---------------------------------------------------------------------------

def require_super_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Only the platform owner (Super Admin) may call this route."""
    if not _is_super_admin_identity(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin privileges required",
        )
    return current_user


def require_tenant_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Tenant Admins (and Super Admin) may call this route."""
    if _is_super_admin_identity(current_user):
        return current_user

    role = _normalize_role(current_user.get("role"))
    if role != ROLE_TENANT_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant Admin privileges required",
        )
    if not current_user.get("tenant_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant Admin must belong to a tenant",
        )
    return current_user


def require_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Any authenticated user may call this route."""
    if not current_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return current_user


# ---------------------------------------------------------------------------
# Cross-tenant guard
# ---------------------------------------------------------------------------

def assert_same_tenant(actor: dict, tenant_id: str) -> None:
    """Raise 403 if actor is trying to touch a different tenant's data."""
    if _is_super_admin_identity(actor):
        return  # Super Admin is above tenant boundaries
    if not actor.get("tenant_id") or actor.get("tenant_id") != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access is not allowed",
        )


# ---------------------------------------------------------------------------
# Scope helper
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class UserScope:
    tenant_id:  Optional[str]
    department: Optional[str]
    role:       str


def get_user_scope(user: dict) -> UserScope:
    """
    Returns the effective query scope for a user:
      - Super Admin  -> unrestricted (no tenant / department filter)
      - Tenant Admin -> tenant-scoped, all departments
      - End User     -> tenant + department scoped
    """
    role       = _normalize_role(user.get("role"))
    tenant_id  = user.get("tenant_id")
    department = user.get("department") or user.get("dept")

    if _is_super_admin_identity(user):
        return UserScope(tenant_id=None, department=None, role=ROLE_SUPER_ADMIN)

    if role == ROLE_TENANT_ADMIN:
        return UserScope(tenant_id=tenant_id, department=None, role=ROLE_TENANT_ADMIN)

    # Default: End User
    return UserScope(tenant_id=tenant_id, department=department, role=ROLE_USER)
