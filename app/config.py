from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProviderName = Literal["ollama", "openai"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    # Switch providers with LLM_PROVIDER=openai | ollama
    llm_provider: LLMProviderName = "openai"

    # OpenAI — default, and what the deployed API uses
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    # Ollama — fully local alternative, no API key needed
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"

    cors_origins: str = "http://localhost:3000"


settings = Settings()
