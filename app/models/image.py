"""Image model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


def generate_image_id():
    """Generate a unique image ID."""
    return str(uuid.uuid4())


class Image(Base):
    """Image model for storing user-uploaded images as base64."""

    __tablename__ = "images"

    id = Column(String(255), primary_key=True, default=generate_image_id, index=True)
    user_id = Column(String(255), ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    image_data = Column(Text, nullable=False)  # Base64 encoded image
    conversation_id = Column(String(255), ForeignKey("conversations.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="images")
    conversation = relationship("Conversation", back_populates="images")
