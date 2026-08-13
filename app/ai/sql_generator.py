from app.ai.json_utils import extract_sql
from app.ai.providers import get_llm_provider
from app.ai.schemas import InferenceMeta
from app.database.schema_context import SCHEMA_CONTEXT

SYSTEM_PROMPT = f"""You generate PostgreSQL SELECT queries and reply with JSON only.

Reply format: {{"sql": "SELECT ..."}}

Schema:
{SCHEMA_CONTEXT}

Rules:
- SELECT only — never INSERT, UPDATE, DELETE, DROP
- Read from a single table; no JOIN, GROUP BY, HAVING, or aggregate functions
- Always end with a LIMIT (max 100)
- Select only the columns needed to answer the request
- Filter borrowers with financial_snapshots.borrower_id = 'borrower_001', or borrowers.name
"""


async def generate_sql(
    intent: str,
    *,
    fix_context: tuple[str, str] | None = None,
) -> tuple[str, InferenceMeta]:
    """Ask the LLM for a SELECT query. Pass fix_context=(failed_sql, error) to retry."""
    user_content = intent
    if fix_context:
        failed_sql, error = fix_context
        user_content = (
            f"{intent}\n\n"
            f"Your previous query failed. Return a corrected single-table SELECT.\n"
            f"Failed SQL: {failed_sql}\n"
            f"Error: {error}"
        )

    provider = get_llm_provider()
    raw, meta = await provider.generate(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=256,
        json_mode=True,
    )
    return extract_sql(raw), meta
