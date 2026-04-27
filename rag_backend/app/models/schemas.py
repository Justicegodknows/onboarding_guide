from pydantic import BaseModel
from typing import List, Optional

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
