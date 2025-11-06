"""Message model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.database import Base


class Message(Base):
    """Message model for storing chat messages."""

    __tablename__ = "messages"

    id = Column(String(255), primary_key=True, index=True)
    conversation_id = Column(String(255), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # 'user', 'assistant'
    content = Column(Text, nullable=False)
    images = Column(JSON, nullable=True, default=list)  # Store list of image IDs
    tool_calls = Column(JSON, nullable=True, default=list)  # Store list of tool calls with structure
    artifact = Column(JSON, nullable=True)  # Store artifact data (design or recommendation)
    meta = Column(JSON, nullable=True)  # Store additional metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
