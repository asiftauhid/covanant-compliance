from typing import Protocol

from app.ai.schemas import InferenceMeta

Message = dict[str, str]


class LLMProvider(Protocol):
    async def generate(
        self,
        messages: list[Message],
        max_tokens: int = 512,
        json_mode: bool = False,
    ) -> tuple[str, InferenceMeta]: ...
