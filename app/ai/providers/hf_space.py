import time

import httpx

from app.ai.providers.base import LLMProvider
from app.ai.schemas import InferenceMeta


class HFSpaceProvider:
    """Calls your self-hosted Qwen service on Hugging Face Spaces."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def generate(self, messages: list[dict[str, str]], max_tokens: int = 512) -> tuple[str, InferenceMeta]:
        start = time.perf_counter()
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(f"{self.base_url}/v1/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        inference_ms = data.get("inference_ms") or int((time.perf_counter() - start) * 1000)

        return data["text"].strip(), InferenceMeta(
            model=data.get("model", "qwen-hf-space"),
            inference_ms=inference_ms,
            provider="hf_space",
        )
