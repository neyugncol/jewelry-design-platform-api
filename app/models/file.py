"""File model."""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from app.db.database import Base


class File(Base):
    """File model for storing uploaded files with short IDs."""

    __tablename__ = "files"

    # Short ID that is easy to reference in LLMs (e.g., "abc123")
    short_id = Column(String(8), primary_key=True, index=True)

    # Original filename
    filename = Column(String(255), nullable=False)

    # File path relative to data volume
    file_path = Column(String(512), nullable=False)

    # MIME type
    content_type = Column(String(100), nullable=False)

    # File size in bytes
    file_size = Column(Integer, nullable=False)

    # Optional user ID who uploaded the file
    user_id = Column(String(255), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
