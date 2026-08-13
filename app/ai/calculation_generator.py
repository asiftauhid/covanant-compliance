import json

from app.ai.json_utils import extract_json
from app.ai.providers import get_llm_provider
from app.ai.schemas import InferenceMeta
from app.covenants.schemas import CovenantRule

SYSTEM_PROMPT = """You compute financial covenant metrics from database values and reply with JSON only.

Reply with exactly these keys:
{"actual": <number>, "formula": "<arithmetic over data keys>", "inputs": {"<data key>": <number>}}

The formula is the important part — it is recomputed to verify your answer.
- It must combine keys from data using only + - * / and parentheses
- Every name in it must be a key of data, copied exactly
- Never use the metric name, the covenant name, the threshold, or a comparison operator

Examples:
  data {"net_operating_income": 118000, "debt_service": 100000}
    -> {"actual": 1.18, "formula": "net_operating_income / debt_service",
        "inputs": {"net_operating_income": 118000, "debt_service": 100000}}
  data {"total_debt": 780000}
    -> {"actual": 780000, "formula": "total_debt", "inputs": {"total_debt": 780000}}

Other rules:
- Copy numbers from data exactly; never invent or round them
- Round actual to 4 decimal places
- If data lacks a value you need, set actual to null and add "error" naming what is missing
"""


async def generate_calculation(
    rule: CovenantRule,
    data: dict[str, float],
    *,
    fix_context: tuple[str, str] | None = None,
) -> tuple[dict, InferenceMeta]:
    """Ask the LLM to compute the covenant metric. Pass fix_context=(response, error) to retry."""
    request: dict[str, object] = {
        "covenant_name": rule.name,
        "metric": rule.metric,
        "source_text": rule.source_text,
        "calculation_request": rule.calculation_request
        or f"Compute {rule.metric} from the provided data",
        "data": data,
    }

    if fix_context:
        previous, error = fix_context
        request["retry_note"] = (
            f"Your previous reply was rejected ({error}). Return JSON with a numeric "
            f"actual, formula, and inputs. Previous reply: {previous}"
        )

    provider = get_llm_provider()
    raw, meta = await provider.generate(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(request)},
        ],
        max_tokens=256,
        json_mode=True,
    )
    return _clean_keys(extract_json(raw)), meta


def _clean_keys(payload: dict) -> dict:
    """Smaller models sometimes emit keys like 'inputs:' — match on the name only."""
    return {str(key).strip().rstrip(":").strip(): value for key, value in payload.items()}
