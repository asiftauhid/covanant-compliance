from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    # LLM: ollama (local) or hf_space (self-hosted on Hugging Face)
    llm_provider: str = "ollama"
    llm_base_url: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"


settings = Settings()
