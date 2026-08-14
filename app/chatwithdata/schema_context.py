"""Schema context for chat-with-data SQL generation."""

from sqlalchemy.orm import Session

from app.database.models import Borrower
from app.database.schema_context import SCHEMA_CONTEXT


def build_chat_schema(db: Session) -> str:
    """Base table schema plus the exact borrower names currently in the database."""
    rows = db.query(Borrower.name, Borrower.industry).order_by(Borrower.name).all()
    if rows:
        roster = "\n".join(f"  - {name} ({industry})" for name, industry in rows)
    else:
        roster = "  (no borrowers loaded)"

    return (
        f"{SCHEMA_CONTEXT}\n\n"
        "Known borrowers — use these exact names when the user refers to a company:\n"
        f"{roster}\n\n"
        "Chat tips:\n"
        "- 'debt' usually means total_debt; 'debt service' means debt_service.\n"
        "- Expand numeric shorthand in SQL (90k -> 90000, 1.2m -> 1200000).\n"
        "- Every comparison or threshold in the question MUST appear in WHERE or HAVING.\n"
        "- For ratios, select the input columns and/or compute them in SQL with NULLIF "
        "to avoid divide-by-zero, e.g. revenue / NULLIF(cash_balance, 0).\n"
        "- When listing companies, JOIN borrowers and return name with the metrics."
    )
