"""
Pipeline 1 — retrieval.

  intent  →  LLM SELECT  →  guardrails  →  PostgreSQL rows
"""

import asyncio
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.sql_generator import generate_sql
from app.database.sql_executor import SQLValidationError, execute_sql

MAX_ATTEMPTS = 2


class RetrievalResult(BaseModel):
    intent: str
    sql: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    inference_ms: int = 0
    model: str | None = None
    error: str | None = None


async def retrieve_data(db: Session, intent: str) -> RetrievalResult:
    """Generate and run a SELECT for the intent, retrying once with the error as feedback."""
    sql: str | None = None
    error: str | None = None

    for attempt in range(MAX_ATTEMPTS):
        fix_context = (sql, error) if attempt and sql and error else None

        try:
            sql, meta = await generate_sql(intent, fix_context=fix_context)
            # Sync driver: run the query off the event loop so parallel checks keep moving.
            rows = await asyncio.to_thread(execute_sql, db, sql)
            return RetrievalResult(
                intent=intent,
                sql=sql,
                rows=rows,
                inference_ms=meta.inference_ms,
                model=meta.model,
            )
        except (SQLValidationError, ValueError) as exc:
            error = str(exc)
        except Exception as exc:
            error = f"Retrieval failed: {exc}"

    return RetrievalResult(intent=intent, sql=sql, error=error)
