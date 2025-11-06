"""Conversation model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Conversation(Base):
    """Conversation model for storing chat sessions."""

    __tablename__ = "conversations"

    id = Column(String(255), primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="conversation", cascade="all, delete-orphan")
