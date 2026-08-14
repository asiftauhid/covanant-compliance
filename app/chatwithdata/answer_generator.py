"""Turn retrieved DB rows into a plain-language answer grounded in that data."""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.ai.providers import get_llm_provider

SYSTEM_PROMPT = """You answer questions about borrower financial data.

Rules:
- Use ONLY the retrieved row sets provided. Do not invent numbers or borrowers.
- If the rows are empty or do not answer the question, say so clearly.
- Do not mention SQL, models, or that you are an AI unless asked.
- Write plain text only. No markdown, no LaTeX, no bold asterisks, no backslash math.
- Open by restating the filter that was applied and how many rows matched it.
  If every company matched, say that explicitly (the filter still applied).
- For multi-company or filtered lists, go company by company.
- When any calculation is needed (ratios, sums, averages, differences, etc.):
  1. Show the work in clear numbered steps.
  2. State the values taken from the data in each step.
  3. Show the arithmetic for each step as plain text, e.g. 420000 / 74000 = 5.6757
  4. After all companies/steps, put the final answer under "Result:".
- Never skip showing the formula inputs when a ratio is requested.
"""


def _json_default(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def _serialize_datasets(datasets: list[dict[str, Any]]) -> str:
    compact = []
    for index, dataset in enumerate(datasets, start=1):
        rows = dataset.get("rows") or []
        compact.append(
            {
                "query": index,
                "intent": dataset.get("intent"),
                "sql": dataset.get("sql"),
                "row_count": len(rows),
                "rows": rows[:50],
            }
        )
    return json.dumps(compact, default=_json_default)


async def generate_answer(
    question: str,
    datasets: list[dict[str, Any]],
    *,
    history: list[dict[str, str]] | None = None,
    calculation: str | None = None,
    constraints: list[str] | None = None,
) -> str:
    """Narrate an answer from one or more retrieved datasets."""
    user_parts: list[str] = []
    if history:
        for turn in history[-6:]:
            user_parts.append(f"{turn['role'].upper()}: {turn['content']}")
        user_parts.append("")

    user_parts.append(f"QUESTION: {question}")
    if constraints:
        user_parts.append(
            "FILTERS THAT MUST BE REFLECTED IN THE ANSWER:\n"
            + "\n".join(f"- {item}" for item in constraints)
        )
    if calculation:
        user_parts.append(f"CALCULATION TO PERFORM: {calculation}")
    user_parts.append(f"RETRIEVED DATASETS:\n{_serialize_datasets(datasets)}")

    provider = get_llm_provider()
    text, _meta = await provider.generate(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(user_parts)},
        ],
        max_tokens=1200,
    )
    return text.strip()
