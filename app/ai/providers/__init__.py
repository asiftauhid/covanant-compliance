from app.ai.providers.hf_space import HFSpaceProvider
from app.ai.providers.ollama import OllamaProvider
from app.config import settings


def get_llm_provider():
    if settings.llm_provider == "hf_space":
        if not settings.llm_base_url:
            raise ValueError("LLM_BASE_URL is required when LLM_PROVIDER=hf_space")
        return HFSpaceProvider(settings.llm_base_url)

    return OllamaProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )
