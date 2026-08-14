"""Check that generated SQL actually applies the user's filters."""

from app.ai.json_utils import extract_json
from app.ai.providers import get_llm_provider

SYSTEM_PROMPT = """You check whether a SELECT query implements the user's filters.

Reply with JSON only:
{"ok": true or false, "missing": ["constraint that is not in the SQL"]}

Rules:
- ok is true only if EVERY required constraint is reflected in the SQL
  (WHERE, JOIN ... ON, or HAVING — equivalent wording is fine).
- ok is false if the SQL returns an unfiltered table when constraints exist.
- missing lists the constraints that are absent. Empty when ok is true.
- Do not invent extra constraints. Only check the list you were given.
"""


async def sql_covers_constraints(
    sql: str,
    constraints: list[str],
    question: str,
) -> tuple[bool, str | None]:
    """True when SQL appears to apply every required constraint."""
    if not constraints:
        return True, None

    provider = get_llm_provider()
    raw, _meta = await provider.generate(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n"
                    f"Required constraints:\n"
                    + "\n".join(f"- {item}" for item in constraints)
                    + f"\n\nSQL:\n{sql}"
                ),
            },
        ],
        max_tokens=200,
        json_mode=True,
    )

    try:
        payload = extract_json(raw)
    except (ValueError, TypeError):
        return True, None

    if payload.get("ok") is True:
        return True, None

    missing = [
        str(item).strip()
        for item in (payload.get("missing") or constraints)
        if str(item).strip()
    ]
    detail = ", ".join(missing) if missing else "required filters were not applied"
    return False, (
        "The SQL does not apply every filter from the question. "
        f"Put these into WHERE (or equivalent): {detail}"
    )
