
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
