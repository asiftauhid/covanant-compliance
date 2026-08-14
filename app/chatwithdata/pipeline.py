"""
Chat with data.

  question → plan (intents + constraints) → guarded SQL (reviewed) → answer
"""

from sqlalchemy.orm import Session

from app.chatwithdata.answer_generator import generate_answer
from app.chatwithdata.planner import plan_retrieval
from app.chatwithdata.schema_context import build_chat_schema
from app.chatwithdata.schemas import ChatMessage, ChatTurnResult
from app.chatwithdata.sql_review import sql_covers_constraints
from app.covenants.retrieval_pipeline import retrieve_data


def _history_for_prompt(history: list[ChatMessage]) -> list[dict[str, str]]:
    return [{"role": message.role, "content": message.content} for message in history]


def _retrieval_intent(
    question: str,
    planned: str,
    constraints: list[str],
    previous_sql: str | None = None,
    review_error: str | None = None,
) -> str:
    parts = [
        "Write one PostgreSQL SELECT that fully satisfies this retrieval intent.",
        "JOIN borrowers when company names are needed.",
        "Include every column required for later ratios/calculations.",
        "You may select computed expressions using NULLIF to avoid divide-by-zero.",
        "'debt' means total_debt unless debt service was requested.",
        "Every user filter must appear in WHERE (or HAVING). Do not return an unfiltered table.",
        "",
        f"User question: {question}",
        f"Retrieval intent: {planned}",
    ]
    if constraints:
        parts.append("Required WHERE constraints — all must appear in the SQL:")
        parts.extend(f"- {item}" for item in constraints)
    if previous_sql and review_error:
        parts.extend(
            [
                "",
                f"Previous SQL:\n{previous_sql}",
                f"Fix this: {review_error}",
            ]
        )
    return "\n".join(parts)


async def _retrieve_once(
    db,
    question: str,
    planned: str,
    constraints: list[str],
    chat_schema: str,
    *,
    previous_sql: str | None = None,
    review_error: str | None = None,
):
    return await retrieve_data(
        db,
        _retrieval_intent(
            question,
            planned,
            constraints,
            previous_sql=previous_sql,
            review_error=review_error,
        ),
        schema_context=chat_schema,
    )


async def chat_with_data(
    db: Session,
    question: str,
    history: list[ChatMessage] | None = None,
) -> ChatTurnResult:
    """Answer a natural-language question using one or more guarded SQL retrievals."""
    cleaned = question.strip()
    if not cleaned:
        return ChatTurnResult(answer="", error="Question is empty")

    prior = history or []
    chat_schema = build_chat_schema(db)

    try:
        intents, constraints, calculation = await plan_retrieval(cleaned, chat_schema)
    except Exception:
        intents, constraints, calculation = [cleaned], [], None

    datasets: list[dict] = []
    errors: list[str] = []
    sql_parts: list[str] = []

    for planned in intents:
        retrieval = await _retrieve_once(db, cleaned, planned, constraints, chat_schema)

        if retrieval.sql and constraints:
            ok, review_error = await sql_covers_constraints(
                retrieval.sql, constraints, cleaned
            )
            if not ok and review_error:
                retrieval = await _retrieve_once(
                    db,
                    cleaned,
                    planned,
                    constraints,
                    chat_schema,
                    previous_sql=retrieval.sql,
                    review_error=review_error,
                )

        if retrieval.sql:
            sql_parts.append(retrieval.sql)
        if retrieval.error:
            errors.append(retrieval.error)
            continue
        datasets.append(
            {
                "intent": planned,
                "sql": retrieval.sql,
                "rows": retrieval.rows,
            }
        )

    combined_sql = "\n\n".join(sql_parts) if sql_parts else None
    all_rows = [row for dataset in datasets for row in dataset["rows"]]

    if not datasets:
        detail = "; ".join(errors) if errors else "No data retrieved"
        return ChatTurnResult(
            answer=f"I could not retrieve data for that question. {detail}",
            sql=combined_sql,
            error=detail,
        )

    try:
        answer = await generate_answer(
            cleaned,
            datasets,
            history=_history_for_prompt(prior),
            calculation=calculation,
            constraints=constraints,
        )
    except Exception as exc:
        return ChatTurnResult(
            answer=f"I retrieved data but could not form an answer: {exc}",
            sql=combined_sql,
            rows=all_rows,
            error=str(exc),
        )

    return ChatTurnResult(
        answer=answer or "No answer was produced from the retrieved data.",
        sql=combined_sql,
        rows=all_rows,
        error="; ".join(errors) if errors else None,
    )
