from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MAILMIND_", extra="ignore")

    database_url: str = "sqlite:///./mailmind.db"
    frontend_url: str = "http://localhost:3000"

    # Provider integration (placeholders for upcoming work)
    gmail_client_id: str | None = None
    gmail_client_secret: str | None = None
    gmail_redirect_uri: str = "http://localhost:8000/api/oauth/gmail/callback"

    # Used to encrypt provider tokens at rest.
    token_encryption_key: str | None = None

    # Optional AI enhancement for label suggestions (user supplies their own key).
    ai_provider: str | None = None  # "gemini" or "openai"
    ai_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()

