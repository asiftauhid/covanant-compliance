"""Database schema description for LLM SQL generation."""

SCHEMA_CONTEXT = """
borrowers
  id (text, PK)             e.g. 'borrower_001'
  name (text)               e.g. 'ABC Trading LLC'
  industry (text)

financial_snapshots         one row per borrower per month
  borrower_id (text)        e.g. 'borrower_001'
  period_start (date)       first day of the month, e.g. '2026-07-01'
  period_end (date)         first day of the next month, e.g. '2026-08-01'
  revenue, ebitda, net_operating_income, cash_balance,
  current_assets, current_liabilities, total_debt, debt_service   (all numeric)

Example — values for borrower_001, period 2026-07:
  SELECT net_operating_income, debt_service
  FROM financial_snapshots
  WHERE borrower_id = 'borrower_001'
    AND period_start = '2026-07-01'
    AND period_end = '2026-08-01'
  LIMIT 100
""".strip()

ALLOWED_TABLES = {"borrowers", "financial_snapshots"}
MAX_ROWS = 100
