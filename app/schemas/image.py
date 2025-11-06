"""Image schemas for request/response models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ImageResponse(BaseModel):
    """Response model for image."""
    id: str = Field(description="Unique identifier for the image")
    user_id: str = Field(description="ID of the user who owns this image")
    filename: str = Field(description="Original filename of the uploaded image")
    content_type: str = Field(description="MIME type of the image (e.g., image/jpeg, image/png)")
    image_data: str = Field(description="Base64 encoded image data")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation this image is associated with")
    created_at: datetime = Field(description="Timestamp when the image was uploaded")

    class Config:
        from_attributes = True


class ImageListResponse(BaseModel):
    """Response model for image list."""
    images: list[ImageResponse] = Field(description="List of images")
    total: int = Field(description="Total number of images")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of images per page")


class GeneratedImageResponse(BaseModel):
    """Response model for generated image."""
    id: str = Field(description="Unique identifier for the generated image")
    conversation_id: str = Field(description="ID of the conversation this generated image belongs to")
    message_id: Optional[str] = Field(None, description="ID of the message that generated this image")
    image_type: str = Field(description="Type of generated image (e.g., 2d, 3d)")
    prompt: str = Field(description="Text prompt used to generate the image")
    image_url: Optional[str] = Field(None, description="URL of the generated image")
    image_path: Optional[str] = Field(None, description="Local file path of the generated image")
    properties: Optional[dict] = Field(None, description="Additional properties of the generated image")
    created_at: datetime = Field(description="Timestamp when the image was generated")

    class Config:
        from_attributes = True
