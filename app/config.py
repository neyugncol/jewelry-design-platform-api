"""Application configuration."""
import random
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Gemini API Configuration
    # You can provide multiple API keys separated by commas in the .env file
    # Example: GEMINI_API_KEYS=key1,key2,key3
    gemini_api_keys: str = "secret"

    # Database Configuration
    database_url: str = "sqlite:///./data/jewelry_designer.db"

    # Application Configuration
    app_name: str = "PNJ Jewelry AI Designer"
    app_version: str = "1.0.0"
    debug: bool = True

    # Gemini Models
    chat_model: str = "gemini-2.5-flash"
    image_model: str = "gemini-2.0-flash-preview-image-generation"

    # Authentication Configuration
    secret_key: str = "your-secret-key-change-this-in-production-use-openssl-rand-hex-32"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"


class GeminiAPIKeyPool:
    """Manager for Gemini API key pool with random selection."""

    def __init__(self, api_keys: str):
        """
        Initialize the API key pool.

        Args:
            api_keys: Comma-separated string of API keys
        """
        # Split by comma and strip whitespace
        self._keys: List[str] = [key.strip() for key in api_keys.split(",") if key.strip()]

        if not self._keys:
            raise ValueError("At least one API key must be provided")

    def get_api_key(self) -> str:
        """
        Get a random API key from the pool.

        Returns:
            A randomly selected API key
        """
        return random.choice(self._keys)

    def get_all_keys(self) -> List[str]:
        """
        Get all API keys in the pool.

        Returns:
            List of all API keys
        """
        return self._keys.copy()

    def get_pool_size(self) -> int:
        """
        Get the number of API keys in the pool.

        Returns:
            Number of API keys
        """
        return len(self._keys)


settings = Settings()
api_key_pool = GeminiAPIKeyPool(settings.gemini_api_keys)
