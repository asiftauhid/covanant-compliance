import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.ai.providers import get_llm_provider
from app.config import settings

app = FastAPI(
    title="Covenant Compliance Monitor",
    description="AI-powered loan covenant compliance API",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
    }


class LLMTestRequest(BaseModel):
    prompt: str = "Reply with exactly: LLM is working."


@app.post("/llm/test")
async def llm_test(body: LLMTestRequest):
    """Quick check that the configured LLM provider responds."""
    provider = get_llm_provider()
    messages = [{"role": "user", "content": body.prompt}]

    try:
        text, meta = await provider.generate(messages, max_tokens=64)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"LLM provider error: {exc}") from exc

    return {
        "text": text,
        "model": meta.model,
        "inference_ms": meta.inference_ms,
        "provider": meta.provider,
    }
