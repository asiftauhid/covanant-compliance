"""Turn retrieved DB rows into a plain-language answer grounded in that data."""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.ai.providers import get_llm_provider

SYSTEM_PROMPT = """You answer questions about borrower financial data in a natural tone.

Rules:
- Use ONLY the retrieved rows. Do not invent numbers or borrowers.
- If nothing matches, say so in one short sentence.
- Do not mention SQL, models, filters, row counts, period_start, or period_end.
- Write plain text. No markdown, no LaTeX.
- Format money and large numbers with commas (610,000 not 610000.0). Drop trailing .0.
- Simple lookup (one company, one figure): one or two sentences. Do not add a Result line.
  Example: ABC Trading LLC's total debt for July 2026 is 610,000.
- Comparison filters or several companies: briefly say who is included, then list them.
- Calculations (ratios, sums, averages):
  1. Numbered steps with the values from the data.
  2. Plain arithmetic, e.g. 420,000 / 74,000 = 5.68
  3. End with a Result: line (once). Do not repeat the same number three times.
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
    if calculation:
        user_parts.append(f"CALCULATION TO PERFORM: {calculation}")
    elif constraints:
        user_parts.append(
            "The user asked for a filtered set. Honour these conditions in who you include, "
            "but do not narrate them as database filters:\n"
            + "\n".join(f"- {item}" for item in constraints)
        )
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
