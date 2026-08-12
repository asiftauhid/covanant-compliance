"""Test Pipeline 2: calculation pipeline + evaluator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.covenants.evaluator import evaluate, evaluate_actual
from app.database.queries import get_financial_snapshot
from app.database.session import SessionLocal
from app.schemas.covenant import CovenantRule

RULES = [
    CovenantRule(
        name="Minimum DSCR",
        metric="dscr",
        operator=">=",
        threshold=1.25,
        source_text="Maintain a Debt Service Coverage Ratio of at least 1.25x.",
        calculation_request="Compute DSCR as net_operating_income / debt_service",
    ),
    CovenantRule(
        name="Minimum Cash Balance",
        metric="cash_balance",
        operator=">=",
        threshold=100_000,
        currency="AED",
        source_text="Maintain unrestricted cash of at least AED 100,000.",
        calculation_request="Return cash_balance",
    ),
]


def snapshot_to_dict(snapshot) -> dict[str, float]:
    return {
        "revenue": float(snapshot.revenue),
        "ebitda": float(snapshot.ebitda),
        "net_operating_income": float(snapshot.net_operating_income),
        "cash_balance": float(snapshot.cash_balance),
        "current_assets": float(snapshot.current_assets),
        "current_liabilities": float(snapshot.current_liabilities),
        "total_debt": float(snapshot.total_debt),
        "debt_service": float(snapshot.debt_service),
    }


def main() -> None:
    db = SessionLocal()
    try:
        snapshot = get_financial_snapshot(db, "borrower_001", "2026-07")
        if snapshot is None:
            print("No snapshot found for borrower_001 / 2026-07")
            return

        data = snapshot_to_dict(snapshot)

        print("=== Full pipeline (calculation pending LLM) ===\n")
        for rule in RULES:
            result = evaluate(rule, data)
            print(f"{result.name}: status={result.status} reason={result.reason}")

        print("\n=== Evaluator only (mock actuals, as if calculation pipeline ran) ===\n")
        mocks = [
            (RULES[0], 1.18, {"net_operating_income": 118_000, "debt_service": 100_000}),
            (RULES[1], 74_000, {"cash_balance": 74_000}),
        ]
        for rule, actual, inputs in mocks:
            result = evaluate_actual(rule, actual, inputs)
            print(f"{result.name}: actual={result.actual} threshold={result.threshold} -> {result.status}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
