"""
Pipeline 0 — extraction.

  loan agreement PDF  →  text  →  LLM  →  CovenantRule list
"""

from pydantic import BaseModel, Field

from app.ai.covenant_extractor import extract_covenants
from app.covenants.schemas import CovenantRule
from app.documents.pdf_parser import extract_text_from_pdf
from app.errors import public_error


class ExtractionResult(BaseModel):
    covenants: list[CovenantRule] = Field(default_factory=list)
    text_chars: int = 0
    inference_ms: int = 0
    model: str = ""
    error: str | None = None


async def extract_covenants_from_pdf(content: bytes) -> ExtractionResult:
    """Parse PDF text and extract structured covenant rules via LLM."""
    try:
        text = extract_text_from_pdf(content)
    except Exception as exc:
        return ExtractionResult(error=f"Could not read PDF: {public_error(exc)}")

    try:
        covenants, meta = await extract_covenants(text)
    except Exception as exc:
        return ExtractionResult(text_chars=len(text), error=f"Covenant extraction failed: {public_error(exc)}")

    return ExtractionResult(
        covenants=covenants,
        text_chars=len(text),
        inference_ms=meta.inference_ms,
        model=meta.model,
    )
