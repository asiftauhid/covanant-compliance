import time

import httpx

from app.ai.providers.base import LLMProvider
from app.ai.schemas import InferenceMeta


class OllamaProvider:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(self, messages: list[dict[str, str]], max_tokens: int = 512) -> tuple[str, InferenceMeta]:
        start = time.perf_counter()
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.1},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        text = data["message"]["content"].strip()
        inference_ms = int((time.perf_counter() - start) * 1000)

        return text, InferenceMeta(
            model=self.model,
            inference_ms=inference_ms,
            provider="ollama",
        )
