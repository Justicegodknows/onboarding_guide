"""
Integrations router — manages external service connections.

Supported integration types:
  email          — SMTP / IMAP credentials for email ingestion or notifications
  jira           — Jira Cloud/Server via API token
  google_calendar — Google Calendar via OAuth service account or API key
  slack          — Slack incoming webhooks or Bot token
  microsoft_teams — Teams incoming webhook
  github         — GitHub App / Personal Access Token
  notion         — Notion integration token
  custom         — Generic key/value config for any other service

Security notes:
  - All endpoints (except health) require a valid JWT.
  - Integration configs (API keys / tokens) are stored as JSON.
    In production, encrypt the `config` column at rest via a KMS service.
  - Org-wide integrations may only be created/modified by ADMINs.
  - Users can manage their own personal integrations freely.
"""

import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import SessionLocal
from app.models.db_models import Integration
from app.models.schemas import IntegrationCreate, IntegrationOut, IntegrationUpdate
from app.services.integration_connectors import test_integration_connectivity

router = APIRouter(prefix="/api/v1/integrations", tags=["Integrations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=List[IntegrationOut])
def list_integrations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List integrations owned by the current user plus all org-wide integrations."""
    owner_email = current_user.get("id")  # JWT sub is the email
    query = db.query(Integration).filter(
        (Integration.owner_email == owner_email) | (Integration.is_org_wide == True)  # noqa: E712
    )
    return query.order_by(Integration.created_at.desc()).all()


@router.get("/all", response_model=List[IntegrationOut])
def list_all_integrations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List every integration. Admin only."""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return db.query(Integration).order_by(Integration.created_at.desc()).all()


@router.post("/", response_model=IntegrationOut, status_code=status.HTTP_201_CREATED)
def create_integration(
    payload: IntegrationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new integration for the current user (or org-wide if admin)."""
    if payload.is_org_wide and current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create org-wide integrations.",
        )

    integration = Integration(
        owner_email=current_user.get("id"),
        integration_type=payload.integration_type,
        name=payload.name,
        config=json.dumps(payload.config),
        status="inactive",
        is_org_wide=payload.is_org_wide,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


@router.get("/{integration_id}", response_model=IntegrationOut)
def get_integration(
    integration_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    integration = _get_owned_integration(integration_id, current_user, db)
    return integration


@router.put("/{integration_id}", response_model=IntegrationOut)
def update_integration(
    integration_id: int,
    payload: IntegrationUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update name, config, or status of an integration."""
    integration = _get_owned_integration(integration_id, current_user, db)

    if payload.name is not None:
        integration.name = payload.name
    if payload.config is not None:
        # Merge new config over existing config so callers can send partial updates
        existing = json.loads(integration.config or "{}")
        existing.update(payload.config)
        integration.config = json.dumps(existing)
    if payload.status is not None:
        integration.status = payload.status
    if payload.is_org_wide is not None:
        if payload.is_org_wide and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can set org-wide flag.",
            )
        integration.is_org_wide = payload.is_org_wide

    integration.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(integration)
    return integration


@router.delete("/{integration_id}", status_code=status.HTTP_200_OK)
def delete_integration(
    integration_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect / delete an integration."""
    integration = _get_owned_integration(integration_id, current_user, db)
    db.delete(integration)
    db.commit()
    return {"message": f"Integration '{integration.name}' disconnected."}


@router.post("/{integration_id}/test", status_code=status.HTTP_200_OK)
def test_integration(
    integration_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test the connectivity of an integration and update its status accordingly."""
    integration = _get_owned_integration(integration_id, current_user, db)
    config = json.loads(integration.config or "{}")

    result = test_integration_connectivity(integration.integration_type, config)

    # Persist the updated status
    integration.status = "active" if result["success"] else "error"
    integration.updated_at = datetime.utcnow()
    db.commit()

    return {
        "integration_id": integration_id,
        "integration_type": integration.integration_type,
        "status": integration.status,
        **result,
    }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_owned_integration(
    integration_id: int,
    current_user: dict,
    db: Session,
) -> Integration:
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found.")
    owner_email = current_user.get("id")
    is_admin = current_user.get("role") == "ADMIN"
    if not is_admin and integration.owner_email != owner_email and not integration.is_org_wide:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return integration
