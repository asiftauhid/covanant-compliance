from app.ai.json_utils import extract_sql
from app.ai.providers import get_llm_provider
from app.ai.schemas import InferenceMeta
from app.database.schema_context import SCHEMA_CONTEXT


def _system_prompt(schema_context: str) -> str:
    return f"""You generate PostgreSQL SELECT queries and reply with JSON only.

Reply format: {{"sql": "SELECT ..."}}

Schema:
{schema_context}

Rules:
- SELECT only — never INSERT, UPDATE, DELETE, DROP
- Only use the tables in the schema above
- JOINs between those tables are allowed when needed (e.g. filter by borrower name)
- Prefer the simplest correct query; skip JOINs when borrower_id is already known
- Aggregates (SUM, COUNT, AVG, MIN, MAX) are allowed when the question needs them
- Always end with a LIMIT (max 100)
- Select only the columns needed to answer the request
- When filtering by company, use the exact borrower names from the schema
- If the request lists required WHERE constraints, every one of them MUST appear
  in the SQL. An unfiltered SELECT is wrong whenever constraints were given.
"""


async def generate_sql(
    intent: str,
    *,
    fix_context: tuple[str, str] | None = None,
    schema_context: str | None = None,
) -> tuple[str, InferenceMeta]:
    """Ask the LLM for a SELECT query. Pass fix_context=(failed_sql, error) to retry."""
    user_content = intent
    if fix_context:
        failed_sql, error = fix_context
        user_content = (
            f"{intent}\n\n"
            f"Your previous query failed. Return a corrected SELECT.\n"
            f"Failed SQL: {failed_sql}\n"
            f"Error: {error}"
        )

    provider = get_llm_provider()
    raw, meta = await provider.generate(
        [
            {"role": "system", "content": _system_prompt(schema_context or SCHEMA_CONTEXT)},
            {"role": "user", "content": user_content},
        ],
        max_tokens=400,
        json_mode=True,
    )
    return extract_sql(raw), meta
