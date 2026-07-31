from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "AI20K Agent"
    app_env: Literal["development", "production", "test"] = "development"
    app_port: int = Field(default=8000, ge=1, le=65535)
    app_host: str = "0.0.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    max_audio_upload_mb: int = Field(default=20, ge=1, le=100)
    max_transcript_chars: int = Field(default=12000, ge=100, le=100000)
    asr_model_name: str = "vinai/PhoWhisper-small"

    # LLM
    llm_provider: Literal["openai", "gemini"] = "openai"
    openai_api_key: str = ""
    model_name: str = "gpt-4o-mini"
    google_api_key: str = ""
    gemini_model_name: str = "gemini-2.0-flash"
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    # Database
    database_url: str = "sqlite:///./data/app.db"

    # Vector Store
    chroma_persist_dir: str = "./data/chroma"

    # MCP
    mcp_clinical_url: str = "http://localhost:8001/mcp"

    # Security
    secret_key: str = "change-me-in-production-use-a-real-secret"

@lru_cache
def get_settings() -> Settings:
    return Settings()
