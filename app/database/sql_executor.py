"""Guardrails for LLM-generated SQL: read-only, single table, bounded rows."""

import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.schema_context import ALLOWED_TABLES, MAX_ROWS

WRITE_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|GRANT|REVOKE"
    r"|EXEC|EXECUTE|MERGE|CALL|COPY|VACUUM|ATTACH|DETACH)\b",
    re.IGNORECASE,
)

# Aggregation and set operations are how the model produces rows we cannot map
# back to a single reporting period, so they are rejected outright.
DISALLOWED_CLAUSES = re.compile(r"\b(GROUP\s+BY|HAVING|UNION|INTERSECT|EXCEPT)\b", re.IGNORECASE)
AGGREGATE_CALL = re.compile(
    r"\b(SUM|COUNT|AVG|MIN|MAX|ARRAY_AGG|STRING_AGG)\s*\(", re.IGNORECASE
)
TABLE_REFERENCE = re.compile(r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.IGNORECASE)
LIMIT_CLAUSE = re.compile(r"\bLIMIT\s+\d+", re.IGNORECASE)


class SQLValidationError(ValueError):
    pass


def validate_sql(sql: str) -> str:
    """Return the query with a LIMIT applied, or raise if it breaks a guardrail."""
    cleaned = " ".join(sql.strip().rstrip(";").split())

    if not cleaned:
        raise SQLValidationError("Empty SQL")
    if ";" in cleaned:
        raise SQLValidationError("Multiple statements are not allowed")
    if WRITE_KEYWORDS.search(cleaned):
        raise SQLValidationError("Only SELECT queries are allowed")
    if not cleaned.upper().startswith("SELECT"):
        raise SQLValidationError("Query must start with SELECT")
    if DISALLOWED_CLAUSES.search(cleaned):
        raise SQLValidationError("GROUP BY, HAVING, and set operations are not allowed")
    if AGGREGATE_CALL.search(cleaned):
        raise SQLValidationError("Aggregate functions are not allowed")

    tables = TABLE_REFERENCE.findall(cleaned)
    if not tables:
        raise SQLValidationError("Query must reference a table")

    unknown = {table.lower() for table in tables} - ALLOWED_TABLES
    if unknown:
        raise SQLValidationError(f"Tables not allowed: {', '.join(sorted(unknown))}")
    if len(tables) > 1:
        raise SQLValidationError("Query must read from a single table — no JOINs")

    if not LIMIT_CLAUSE.search(cleaned):
        cleaned = f"{cleaned} LIMIT {MAX_ROWS}"

    return cleaned


def execute_sql(db: Session, sql: str) -> list[dict]:
    """Validate then run a SELECT, leaving the session usable if the query fails."""
    safe_sql = validate_sql(sql)
    try:
        rows = db.execute(text(safe_sql)).mappings().all()
    except Exception:
        # Postgres aborts the transaction on error; without this the next
        # covenant check on this session would fail too.
        db.rollback()
        raise

    return [dict(row) for row in rows]
