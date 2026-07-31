import os

from langchain_core.language_models import BaseChatModel

from src.config import get_settings


def get_llm() -> BaseChatModel:
    settings = get_settings()

    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.gemini_model_name,
            google_api_key=settings.google_api_key,
            temperature=settings.llm_temperature,
        )

    if settings.llm_provider == "openai":
        api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Set it in .env or as an environment variable."
            )
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.model_name,
            api_key=api_key,
            temperature=settings.llm_temperature,
        )

    raise ValueError(
        f"Unsupported LLM provider: {settings.llm_provider}"
    )
