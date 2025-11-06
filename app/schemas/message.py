"""Message schemas."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.schemas.artifact import Artifact


class Message(BaseModel):
    """Message schema."""

    id: str = Field(description="Unique identifier for the message")
    conversation_id: str = Field(description="ID of the conversation this message belongs to")
    created_at: datetime = Field(description="Timestamp when the message was created")
    role: str = Field(pattern="^(user|assistant)$", description="Role of the message sender (user or assistant)")
    content: str = Field(description="Text content of the message")
    images: list[str] = Field(default_factory=list, description="List of image IDs associated with this message")
    tool_calls: list[dict[str, Any]] = Field(default_factory=list, description="List of tool calls made during message processing")
    artifact: Artifact | None = Field(None, description="Artifact attached to this message (design or recommendation)")
    meta: dict[str, Any] | None = Field(None, description="Additional metadata for the message")

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Schema for chat request."""

    conversation_id: str = Field(description="ID of the conversation to send the message to")
    message: str = Field(min_length=1, description="Text content of the user message")
    images: list[str] = Field(default_factory=list, description="List of image IDs to attach to the the message. Upload images first using the image upload endpoint.")
    artifact: Artifact | None = Field(None, description="Optional artifact to attach to the message")


class ChatResponse(BaseModel):
    """Schema for chat response."""

    conversation_id: str = Field(description="ID of the conversation")
    user_message: Message = Field(description="The user's message")
    assistant_message: Message = Field(description="The assistant's response message")
