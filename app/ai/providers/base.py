from typing import Protocol

from app.ai.schemas import InferenceMeta


class LLMProvider(Protocol):
    async def generate(self, messages: list[dict[str, str]], max_tokens: int = 512) -> tuple[str, InferenceMeta]: ...
