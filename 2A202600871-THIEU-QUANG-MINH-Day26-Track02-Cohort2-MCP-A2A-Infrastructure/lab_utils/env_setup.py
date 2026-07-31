"""Load .env từ project root — dùng cho mọi agent (orchestrator + A2A specialists)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"


def load_lab_env() -> None:
    """Nạp GOOGLE_API_KEY và biến lab từ .env (idempotent)."""
    load_dotenv(ENV_FILE)
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")


def require_api_key() -> None:
    """Raise sớm nếu thiếu API key (tránh lỗi khó hiểu lúc gọi Gemini)."""
    load_lab_env()
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            f"Thiếu GOOGLE_API_KEY. Đặt trong {ENV_FILE} — "
            "lấy key tại https://aistudio.google.com/app/apikey"
        )
