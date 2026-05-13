from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    department = Column(String)
    start_date = Column(Date)
    onboarding_progress = relationship("OnboardingProgress", back_populates="user")

class AuthUser(Base):
    __tablename__ = "auth_users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="USER")
    dept = Column(String, nullable=False, default="General")
    display_name = Column(String, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class OnboardingProgress(Base):
    __tablename__ = "onboarding_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    step = Column(Integer)
    status = Column(String)
    user = relationship("User", back_populates="onboarding_progress")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    started_at = Column(Date)
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    sender = Column(String)
    content = Column(Text)
    intent = Column(String)
    sources = Column(Text)
    session = relationship("ChatSession", back_populates="messages")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(Date)
    document_metadata = Column("metadata", Text)

class Escalation(Base):
    __tablename__ = "escalations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String)
    created_at = Column(Date)
    resolved_at = Column(Date, nullable=True)
    ticket = Column(Text)


class Integration(Base):
    """Stores user-configured external integrations (email, Jira, calendar, Slack, etc.)."""
    __tablename__ = "integrations"
    id = Column(Integer, primary_key=True, index=True)
    # Owner of the integration — NULL means org-wide (admin-managed)
    owner_email = Column(String, nullable=True, index=True)
    # One of: email | jira | google_calendar | slack | microsoft_teams | github | notion | custom
    integration_type = Column(String, nullable=False)
    # Human-readable label set by the user
    name = Column(String, nullable=False)
    # JSON blob with provider-specific config (API keys, OAuth tokens, server URLs, etc.)
    # In a production system this should be encrypted at rest via a KMS key
    config = Column(Text, nullable=False, default="{}")
    # active | inactive | error
    status = Column(String, nullable=False, default="inactive")
    is_org_wide = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

