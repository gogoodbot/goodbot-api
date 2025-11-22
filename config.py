"""
Application configuration management using pydantic-settings
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # JWT Configuration
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_milliseconds: int

    # Database Configuration
    database_url: str
    database_api_key: str

    # Google AI Configuration
    google_api_key: str

    # CORS Configuration
    cors_origins: str = "http://localhost,http://localhost:3000,http://localhost:8080"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance
    Using lru_cache ensures we only load settings once
    """
    return Settings()
