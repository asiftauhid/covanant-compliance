"""Test the configured LLM provider."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.providers import get_llm_provider, get_provider_info


async def main() -> None:
    info = get_provider_info()
    print(f"Provider: {info['llm_provider']}")
    print(f"Model:    {info['model']}")
    print(f"Endpoint: {info['endpoint']}")

    provider = get_llm_provider()
    text, meta = await provider.generate(
        [{"role": "user", "content": "Reply with exactly: LLM is working."}],
        max_tokens=32,
    )
    print(f"\nResponse: {text}")
    print(f"Provider: {meta.provider} | Model: {meta.model} | {meta.inference_ms}ms")


if __name__ == "__main__":
    asyncio.run(main())
