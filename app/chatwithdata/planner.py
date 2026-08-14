"""Plan retrieval intents and the filters the SQL must honour."""

from app.ai.json_utils import extract_json
from app.ai.providers import get_llm_provider

SYSTEM_PROMPT = """You plan how to answer a borrower-data question using SQL retrieval.

Reply with JSON only:
{
  "intents": ["natural-language description of SELECT #1"],
  "constraints": ["SQL WHERE condition the query MUST include", "..."],
  "calculation": "what to compute from the retrieved rows, or null"
}

Rules:
- Each intent must be answerable by one SELECT over borrowers / financial_snapshots.
- Prefer ONE intent when a single JOIN query can return all needed columns and filters.
- Use 2-3 intents only when the question needs clearly separate lookups.
- When the user asks for a ratio or derived metric, the intent must fetch every input
  column (e.g. revenue AND cash_balance).
- "debt" means total_debt unless the user says debt service.
- Include borrower name via JOIN when listing companies.
- If a period/month is not stated, use the latest available period — do not invent dates.
- constraints: extract EVERY filter the user stated (thresholds, names, industries,
  periods, comparisons). Write each as a SQL predicate using real column names
  (e.g. total_debt > 90000). Expand shorthand like 90k to a number.
  If the user stated no filter, return an empty list.
- Never drop a user filter. If unsure which column, pick the closest schema column
  and still keep the comparison.
"""


async def plan_retrieval(
    question: str, schema_context: str
) -> tuple[list[str], list[str], str | None]:
    """Return (intents, required WHERE constraints, calculation notes)."""
    provider = get_llm_provider()
    raw, _meta = await provider.generate(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Schema:\n{schema_context}\n\n"
                    f"Question: {question}"
                ),
            },
        ],
        max_tokens=500,
        json_mode=True,
    )

    try:
        payload = extract_json(raw)
    except (ValueError, TypeError):
        return [question], [], None

    intents = [
        str(item).strip()
        for item in (payload.get("intents") or [])
        if str(item).strip()
    ]
    if not intents:
        intents = [question]

    constraints = [
        str(item).strip()
        for item in (payload.get("constraints") or [])
        if str(item).strip()
    ]

    calculation = payload.get("calculation")
    if calculation is not None:
        calculation = str(calculation).strip() or None

    return intents[:3], constraints, calculation
