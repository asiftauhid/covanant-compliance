"""Test the configured LLM provider (Ollama local or HF Space)."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.providers import get_llm_provider
from app.config import settings


async def main() -> None:
    print(f"Provider: {settings.llm_provider}")
    if settings.llm_provider == "hf_space":
        print(f"URL: {settings.llm_base_url}")
    else:
        print(f"Ollama: {settings.ollama_base_url} / {settings.ollama_model}")

    provider = get_llm_provider()
    text, meta = await provider.generate(
        [{"role": "user", "content": "Reply with exactly: LLM is working."}],
        max_tokens=32,
    )
    print(f"\nResponse: {text}")
    print(f"Model: {meta.model} | {meta.inference_ms}ms | provider={meta.provider}")


if __name__ == "__main__":
    asyncio.run(main())
