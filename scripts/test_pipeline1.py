"""Test Pipeline 1: LLM SQL retrieval."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.covenants.retrieval_pipeline import retrieve_data
from app.database.session import SessionLocal

INTENT = (
    "Get net_operating_income and debt_service for borrower_001 "
    "for the monthly period 2026-07."
)


async def main() -> None:
    db = SessionLocal()
    try:
        print(f"Intent: {INTENT}\n")
        result = await retrieve_data(db, INTENT)

        if result.error:
            print(f"Error: {result.error}")
            return

        print(f"SQL ({result.inference_ms}ms, {result.model}):\n{result.sql}\n")
        print(f"Rows: {result.rows}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
