"""
Database Models
SQLAlchemy models for document metadata and collections.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Collection(Base):
    """
    Represents a document collection/session.
    Users can create multiple collections to organize different document sets.
    """
    __tablename__ = "collections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to documents
    documents = relationship("Document", back_populates="collection", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Collection(id={self.id}, name='{self.name}', docs={len(self.documents)})>"


class Document(Base):
    """
    Represents a document's metadata.
    The actual document chunks are stored in ChromaDB vector store.
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False, index=True)
    chunks_count = Column(Integer, default=0, nullable=False)
    chunk_size = Column(Integer, nullable=False)  # Chunk size parameter used
    chunk_overlap = Column(Integer, nullable=False)  # Overlap parameter used
    vector_ids_prefix = Column(String(255), nullable=False)  # Prefix for vector store IDs
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to collection
    collection = relationship("Collection", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', collection_id={self.collection_id})>"
