"""User model."""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    """User model for storing user information and authentication."""

    __tablename__ = "users"

    id = Column(String(255), primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    gender = Column(String(20), nullable=True)  # 'male', 'female', 'other'
    age = Column(Integer, nullable=True)
    marital_status = Column(String(20), nullable=True)  # 'single', 'married', 'engaged'
    segment = Column(String(20), nullable=True)  # 'economic', 'middle', 'premium', 'luxury'
    region = Column(String(20), nullable=True)  # 'north', 'central', 'south', 'foreign'
    nationality = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
