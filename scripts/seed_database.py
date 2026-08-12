"""Seed Neon/Postgres with synthetic UAE SME borrowers and monthly snapshots."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.models import Borrower, FinancialSnapshot
from app.database.session import SessionLocal

PERIOD_START = date(2026, 7, 1)
PERIOD_END = date(2026, 8, 1)

BORROWERS = [
    ("borrower_001", "ABC Trading LLC", "Retail"),
    ("borrower_002", "Gulf Logistics FZE", "Logistics"),
    ("borrower_003", "Desert Tech Solutions", "Technology"),
    ("borrower_004", "Emirates Catering Co", "Hospitality"),
    ("borrower_005", "Al Noor Construction", "Construction"),
    ("borrower_006", "Marina Retail Group", "Retail"),
    ("borrower_007", "Falcon Manufacturing", "Manufacturing"),
    ("borrower_008", "Palm Healthcare Supplies", "Healthcare"),
    ("borrower_009", "Summit Property Holdings", "Real Estate"),
    ("borrower_010", "Blue Dhow Trading", "Import/Export"),
]

# Each tuple: revenue, ebitda, noi, cash, current_assets, current_liabilities, total_debt, debt_service
# Designed so covenant checks produce compliant / warning / breached mixes.
SNAPSHOTS = {
    "borrower_001": (420_000, 85_000, 118_000, 74_000, 280_000, 225_000, 610_000, 100_000),
    "borrower_002": (950_000, 210_000, 260_000, 185_000, 520_000, 310_000, 480_000, 95_000),
    "borrower_003": (610_000, 120_000, 128_000, 112_000, 390_000, 280_000, 420_000, 98_000),
    "borrower_004": (330_000, 62_000, 70_000, 45_000, 210_000, 195_000, 720_000, 88_000),
    "borrower_005": (1_200_000, 145_000, 160_000, 98_000, 680_000, 540_000, 890_000, 130_000),
    "borrower_006": (275_000, 48_000, 55_000, 105_000, 240_000, 180_000, 390_000, 72_000),
    "borrower_007": (880_000, 175_000, 190_000, 62_000, 450_000, 360_000, 650_000, 115_000),
    "borrower_008": (510_000, 98_000, 112_000, 130_000, 320_000, 250_000, 505_000, 84_000),
    "borrower_009": (1_450_000, 280_000, 305_000, 220_000, 910_000, 620_000, 1_100_000, 175_000),
    "borrower_010": (390_000, 72_000, 80_000, 38_000, 260_000, 230_000, 780_000, 92_000),
}


def seed() -> None:
    db = SessionLocal()
    try:
        db.query(FinancialSnapshot).delete()
        db.query(Borrower).delete()
        db.commit()

        for borrower_id, name, industry in BORROWERS:
            db.add(Borrower(id=borrower_id, name=name, industry=industry))

        for borrower_id, metrics in SNAPSHOTS.items():
            revenue, ebitda, noi, cash, assets, liabilities, debt, debt_service = metrics
            db.add(
                FinancialSnapshot(
                    borrower_id=borrower_id,
                    period_start=PERIOD_START,
                    period_end=PERIOD_END,
                    revenue=revenue,
                    ebitda=ebitda,
                    net_operating_income=noi,
                    cash_balance=cash,
                    current_assets=assets,
                    current_liabilities=liabilities,
                    total_debt=debt,
                    debt_service=debt_service,
                )
            )

        db.commit()
        print(f"Seeded {len(BORROWERS)} borrowers and {len(SNAPSHOTS)} snapshots for 2026-07.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
