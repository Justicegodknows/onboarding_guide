from pydantic import BaseModel
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    question: str
    history: Optional[List[str]] = None

class ChatResponse(BaseModel):
    answer: str

class DocumentUploadRequest(BaseModel):
    filename: str
    content: str

class DocumentUploadResponse(BaseModel):
    document_id: str

class OnboardingProgress(BaseModel):
    step: int
    status: str


class TrainerRequest(BaseModel):
    question: str
    history: Optional[List[str]] = None


class TrainerResponse(BaseModel):
    answer: str


class DepartmentInfo(BaseModel):
    id: str
    name: str
    description: str
    info: str
    persona_system_prompt: str
    trainer_persona_prompt: str


class DepartmentChatRequest(BaseModel):
    question: str
    history: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Integration schemas
# ---------------------------------------------------------------------------

IntegrationType = Literal[
    "email",
    "jira",
    "google_calendar",
    "slack",
    "microsoft_teams",
    "github",
    "notion",
    "custom",
]


class IntegrationCreate(BaseModel):
    integration_type: IntegrationType
    name: str
    config: Dict[str, Any] = {}
    is_org_wide: bool = False


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[Literal["active", "inactive"]] = None
    is_org_wide: Optional[bool] = None


class IntegrationOut(BaseModel):
    id: int
    owner_email: Optional[str]
    integration_type: str
    name: str
    status: str
    is_org_wide: bool
    created_at: datetime
    updated_at: datetime
    # config is intentionally omitted from response to avoid leaking secrets

    class Config:
        from_attributes = True

