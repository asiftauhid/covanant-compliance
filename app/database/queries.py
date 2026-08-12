from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import FinancialSnapshot


def get_financial_snapshot(db: Session, borrower_id: str, period: str) -> FinancialSnapshot | None:
    """Fetch the financial snapshot for a borrower and YYYY-MM period."""
    year, month = period.split("-")
    period_start = date(int(year), int(month), 1)
    if int(month) == 12:
        period_end = date(int(year) + 1, 1, 1)
    else:
        period_end = date(int(year), int(month) + 1, 1)

    stmt = (
        select(FinancialSnapshot)
        .where(
            FinancialSnapshot.borrower_id == borrower_id,
            FinancialSnapshot.period_start == period_start,
            FinancialSnapshot.period_end == period_end,
        )
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()
