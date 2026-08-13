import time

from app.ai.providers.base import Message
from app.ai.providers.http_client import get_client
from app.ai.schemas import InferenceMeta


class OpenAIProvider:
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate(
        self,
        messages: list[Message],
        max_tokens: int = 512,
        json_mode: bool = False,
    ) -> tuple[str, InferenceMeta]:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        start = time.perf_counter()
        response = await get_client().post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"].strip(), InferenceMeta(
            model=self.model,
            inference_ms=int((time.perf_counter() - start) * 1000),
            provider="openai",
        )
