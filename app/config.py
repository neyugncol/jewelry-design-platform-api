"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Gemini API Configuration
    gemini_api_key: str = "secret"

    # Database Configuration
    database_url: str = "sqlite:///./data/jewelry_designer.db"

    # Application Configuration
    app_name: str = "PNJ Jewelry AI Designer"
    app_version: str = "1.0.0"
    debug: bool = True

    # Gemini Models
    chat_model: str = "gemini-2.0-flash"
    image_model: str = "gemini-2.5-flash-image"

    # Authentication Configuration
    secret_key: str = "your-secret-key-change-this-in-production-use-openssl-rand-hex-32"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"


settings = Settings()
