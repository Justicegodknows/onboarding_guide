
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base


class KnowledgeCategory(Base):
    __tablename__ = "knowledge_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    chunk_count = Column(Integer, default=0)
    what_it_covers = Column(Text)
    chunks = relationship("KnowledgeChunk", back_populates="category")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String, unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("knowledge_categories.id"))
    topic = Column(String)
    title = Column(String)
    content = Column(Text)
    tags = Column(Text)  # JSON-encoded list of tags
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    category = relationship("KnowledgeCategory", back_populates="chunks")

class KnowledgeSourceDocument(Base):
    __tablename__ = "knowledge_source_documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)
    description = Column(Text)
    uploaded_at = Column(DateTime)


class TrainerSourceSnapshot(Base):
    __tablename__ = "trainer_source_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String, unique=True, nullable=False)
    source_type = Column(String, nullable=False)  # website | youtube | other
    title = Column(String)
    content = Column(Text)
    content_hash = Column(String)
    fetched_at = Column(DateTime)


class TrainerResponseMemory(Base):
    __tablename__ = "trainer_response_memory"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    question_key = Column(String, unique=True, nullable=False)
    answer = Column(Text, nullable=False)
    source_digest = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
