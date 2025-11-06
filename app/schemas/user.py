"""User schemas."""
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    """Schema for user in requests (legacy, for backward compatibility)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the user")
    name: str | None = Field(None, description="Full name of the user", examples=["Nguyễn Bảo Ngọc"])
    gender: Literal["male", "female", "other"] | None = Field(None, description="Gender of the user", examples=["female"])
    age: int | None = Field(None, ge=0, le=150, description="Age of the user in years", examples=[28])
    marital_status: Literal["single", "married", "engaged"] | None = Field(None, description="Marital status of the user", examples=["single"])
    segment: Literal["economic", "middle", "premium", "luxury"] | None = Field(None, description="Customer segment classification", examples=["middle"])
    region: Literal["north", "central", "south", "foreign"] | None = Field(None, description="Geographical region of the user", examples=["south"])
    nationality: str | None = Field(None, description="Nationality of the user", examples=["Vietnamese"])


class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(description="User email address", examples=["user@example.com"])
    password: str = Field(min_length=8, description="User password (min 8 characters)", examples=["SecurePass123!"])
    name: str | None = Field(None, description="Full name of the user", examples=["Nguyễn Bảo Ngọc"])
    gender: Literal["male", "female", "other"] | None = Field(None, description="Gender of the user", examples=["female"])
    age: int | None = Field(None, ge=0, le=150, description="Age of the user in years", examples=[28])
    marital_status: Literal["single", "married", "engaged"] | None = Field(None, description="Marital status of the user", examples=["single"])
    segment: Literal["economic", "middle", "premium", "luxury"] | None = Field(None, description="Customer segment classification", examples=["middle"])
    region: Literal["north", "central", "south", "foreign"] | None = Field(None, description="Geographical region of the user", examples=["south"])
    nationality: str | None = Field(None, description="Nationality of the user", examples=["Vietnamese"])


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password")


class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Schema for token payload data."""
    user_id: str | None = Field(None, description="User ID from token")


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str = Field(description="Unique identifier for the user")
    email: str = Field(description="User email address")
    name: str | None = Field(None, description="Full name of the user")
    gender: Literal["male", "female", "other"] | None = Field(None, description="Gender of the user")
    age: int | None = Field(None, description="Age of the user in years")
    marital_status: Literal["single", "married", "engaged"] | None = Field(None, description="Marital status of the user")
    segment: Literal["economic", "middle", "premium", "luxury"] | None = Field(None, description="Customer segment classification")
    region: Literal["north", "central", "south", "foreign"] | None = Field(None, description="Geographical region of the user")
    nationality: str | None = Field(None, description="Nationality of the user")
    is_active: bool = Field(description="Whether the user account is active")
    created_at: datetime = Field(description="Timestamp when user was created")
    updated_at: datetime = Field(description="Timestamp when user was last updated")

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    name: str | None = Field(None, description="Full name of the user")
    gender: Literal["male", "female", "other"] | None = Field(None, description="Gender of the user")
    age: int | None = Field(None, ge=0, le=150, description="Age of the user in years")
    marital_status: Literal["single", "married", "engaged"] | None = Field(None, description="Marital status of the user")
    segment: Literal["economic", "middle", "premium", "luxury"] | None = Field(None, description="Customer segment classification")
    region: Literal["north", "central", "south", "foreign"] | None = Field(None, description="Geographical region of the user")
    nationality: str | None = Field(None, description="Nationality of the user")
