from typing import Literal

from app.ai.providers.base import LLMProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openai import OpenAIProvider
from app.config import settings

ProviderName = Literal["ollama", "openai"]


def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider.lower()

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            base_url=settings.openai_base_url,
        )

    if provider == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}. Use 'ollama' or 'openai'.")


def get_provider_info() -> dict[str, str]:
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return {
            "llm_provider": "openai",
            "model": settings.openai_model,
            "endpoint": settings.openai_base_url,
        }
    return {
        "llm_provider": "ollama",
        "model": settings.ollama_model,
        "endpoint": settings.ollama_base_url,
    }
