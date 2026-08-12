from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Borrower(Base):
    __tablename__ = "borrowers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    industry: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    snapshots: Mapped[list["FinancialSnapshot"]] = relationship(
        back_populates="borrower"
    )


class FinancialSnapshot(Base):
    __tablename__ = "financial_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    borrower_id: Mapped[str] = mapped_column(
        ForeignKey("borrowers.id"), nullable=False, index=True
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    revenue: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    ebitda: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    net_operating_income: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    cash_balance: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    current_assets: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    current_liabilities: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    total_debt: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    debt_service: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    borrower: Mapped["Borrower"] = relationship(back_populates="snapshots")