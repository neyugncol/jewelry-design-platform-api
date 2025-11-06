"""Conversation schemas."""
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.message import Message


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    title: str = Field(min_length=1, max_length=500, description="Title of the conversation", examples=["New jewelry design consultation"])


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: str = Field(description="Unique identifier for the conversation")
    user_id: str = Field(description="ID of the user who owns this conversation")
    title: str = Field(description="Title of the conversation")
    created_at: datetime = Field(description="Timestamp when the conversation was created")
    updated_at: datetime = Field(description="Timestamp when the conversation was last updated")

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Schema for listing conversations."""

    conversations: list[ConversationResponse] = Field(description="List of conversations")
    total: int = Field(description="Total number of conversations")


class ConversationDetailResponse(ConversationResponse):
    """Schema for detailed conversation with messages."""

    messages: list[Message] = Field(default_factory=list, description="List of messages in the conversation")

    class Config:
        from_attributes = True
