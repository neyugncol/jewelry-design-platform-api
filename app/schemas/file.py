"""File schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    short_id: str = Field(description="Short ID for easy reference in LLM (e.g., 'abc123')")
    filename: str = Field(description="Original filename")
    content_type: str = Field(description="MIME type of the file")
    file_size: int = Field(description="File size in bytes")
    created_at: datetime = Field(description="Upload timestamp")

    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    """Schema for file metadata response."""
    short_id: str = Field(description="Short ID for easy reference in LLM")
    filename: str = Field(description="Original filename")
    file_path: str = Field(description="File path relative to data volume")
    content_type: str = Field(description="MIME type of the file")
    file_size: int = Field(description="File size in bytes")
    user_id: str | None = Field(None, description="User ID who uploaded the file")
    created_at: datetime = Field(description="Upload timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """Schema for file list response."""
    files: list[FileResponse] = Field(description="List of files")
    total: int = Field(description="Total number of files")
