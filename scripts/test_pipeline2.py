"""Test Pipeline 2: LLM calculation + deterministic evaluation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.covenants.compliance_pipeline import check_compliance
from app.covenants.schemas import CovenantRule
from app.database.session import SessionLocal

DSCR_RULE = CovenantRule(
    name="Minimum DSCR",
    metric="dscr",
    operator=">=",
    threshold=1.25,
    source_text="Borrower shall maintain a Debt Service Coverage Ratio of at least 1.25x.",
    calculation_request="Calculate DSCR as net_operating_income divided by debt_service.",
)

INTENT = (
    "Get net_operating_income and debt_service for borrower_001 "
    "for the monthly period 2026-07."
)


async def main() -> None:
    db = SessionLocal()
    try:
        print(f"Covenant: {DSCR_RULE.name} {DSCR_RULE.operator} {DSCR_RULE.threshold}")
        print(f"Intent: {INTENT}\n")

        result = await check_compliance(db, DSCR_RULE, INTENT)
        retrieval = result.retrieval
        evaluation = result.evaluation

        if retrieval.error:
            print(f"Retrieval error: {retrieval.error}")
            return

        print(f"SQL ({retrieval.inference_ms}ms, {retrieval.model}):\n{retrieval.sql}\n")
        print(f"Rows: {retrieval.rows}\n")

        print(f"Status: {evaluation.status}")
        print(f"Actual: {evaluation.actual} (threshold {evaluation.threshold})")
        print(f"Inputs: {evaluation.inputs}")
        if evaluation.reason:
            print(f"Reason: {evaluation.reason}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
