"""
Orchestration: PDF → covenants → retrieval → calculation → verdict.
"""

import asyncio
from datetime import date
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.covenants.evaluator import evaluate, undetermined
from app.covenants.extraction_pipeline import (
    ExtractionResult,
    extract_covenants_from_pdf,
)
from app.covenants.numeric import numeric_map
from app.covenants.retrieval_pipeline import RetrievalResult, retrieve_data
from app.covenants.schemas import CovenantRule, EvaluationResult
from app.database.session import SessionLocal


class ComplianceCheckResult(BaseModel):
    retrieval: RetrievalResult
    evaluation: EvaluationResult


class CovenantAnalysisItem(BaseModel):
    covenant: CovenantRule
    intent: str
    check: ComplianceCheckResult


class LoanAnalysisResult(BaseModel):
    borrower_id: str
    period: str
    extraction: ExtractionResult
    results: list[CovenantAnalysisItem] = Field(default_factory=list)


def period_bounds(period: str) -> tuple[date, date]:
    """'2026-07' → (2026-07-01, 2026-08-01), matching the snapshot convention."""
    try:
        year, month = (int(part) for part in period.split("-", 1))
        start = date(year, month, 1)
    except ValueError as exc:
        raise ValueError(f"Period must look like '2026-07', got '{period}'") from exc

    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


def build_retrieval_intent(rule: CovenantRule, borrower_id: str, period: str) -> str:
    """
    Describe the rows to fetch. Which columns are needed comes from the covenant's
    own calculation_request, so the LLM — not this code — maps metrics to columns.
    """
    start, end = period_bounds(period)
    calculation = rule.calculation_request or f"Compute {rule.metric} ({rule.name})"

    return (
        f"Covenant: {rule.name}. {calculation}\n"
        f"Select only the financial_snapshots columns that calculation needs, for "
        f"borrower_id = '{borrower_id}' with period_start = '{start}' and "
        f"period_end = '{end}'. Return a single row."
    )


def rows_to_data(rows: list[dict[str, Any]]) -> dict[str, float]:
    """
    Flatten the first result row into a float map for calculation. Non-numeric
    columns are dropped, because the model sometimes also selects dates or names.
    """
    return numeric_map(rows[0]) if rows else {}


async def check_compliance(
    db: Session, rule: CovenantRule, intent: str
) -> ComplianceCheckResult:
    """Retrieval → LLM calculation → deterministic verdict for one covenant."""
    retrieval = await retrieve_data(db, intent)

    if retrieval.error:
        return ComplianceCheckResult(
            retrieval=retrieval,
            evaluation=undetermined(
                rule, "insufficient_data", f"Data retrieval failed: {retrieval.error}"
            ),
        )

    data = rows_to_data(retrieval.rows)
    if not data:
        return ComplianceCheckResult(
            retrieval=retrieval,
            evaluation=undetermined(
                rule, "insufficient_data", "Query returned no numeric values for this period"
            ),
        )

    return ComplianceCheckResult(
        retrieval=retrieval, evaluation=await evaluate(rule, data)
    )


async def _analyze_covenant(
    rule: CovenantRule, borrower_id: str, period: str
) -> CovenantAnalysisItem:
    """Check one covenant; an unexpected failure degrades to manual_review, not a 500."""
    try:
        intent = build_retrieval_intent(rule, borrower_id, period)
    except ValueError as exc:
        return CovenantAnalysisItem(
            covenant=rule,
            intent="",
            check=ComplianceCheckResult(
                retrieval=RetrievalResult(intent="", error=str(exc)),
                evaluation=undetermined(rule, "insufficient_data", str(exc)),
            ),
        )

    # A Session is not safe to share across concurrent tasks, so each gets its own.
    db = SessionLocal()
    try:
        check = await check_compliance(db, rule, intent)
    except Exception as exc:
        check = ComplianceCheckResult(
            retrieval=RetrievalResult(intent=intent, error=str(exc)),
            evaluation=undetermined(rule, "manual_review", f"Check failed: {exc}"),
        )
    finally:
        db.close()

    return CovenantAnalysisItem(covenant=rule, intent=intent, check=check)


async def analyze_loan_agreement(
    pdf_content: bytes,
    borrower_id: str,
    period: str,
) -> LoanAnalysisResult:
    """Extract covenants from a PDF, then check them all in parallel."""
    extraction = await extract_covenants_from_pdf(pdf_content)

    if extraction.error or not extraction.covenants:
        return LoanAnalysisResult(
            borrower_id=borrower_id, period=period, extraction=extraction
        )

    results = await asyncio.gather(
        *(
            _analyze_covenant(covenant, borrower_id, period)
            for covenant in extraction.covenants
        )
    )

    return LoanAnalysisResult(
        borrower_id=borrower_id,
        period=period,
        extraction=extraction,
        results=list(results),
    )
