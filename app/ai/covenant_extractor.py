from pydantic import ValidationError

from app.ai.json_utils import extract_json
from app.ai.providers import get_llm_provider
from app.ai.schemas import InferenceMeta
from app.covenants.schemas import CovenantRule

SYSTEM_PROMPT = """You extract financial covenants from loan agreement text and reply with JSON only.

Reply format:
{
  "covenants": [
    {
      "name": "Minimum DSCR",
      "metric": "dscr",
      "operator": ">=",
      "threshold": 1.25,
      "currency": null,
      "frequency": "monthly",
      "source_text": "exact clause from the document",
      "calculation_request": "Calculate DSCR as net_operating_income divided by debt_service"
    }
  ]
}

Rules:
- operator must be one of: >=, <=, >, <
- metric is a short snake_case identifier (dscr, current_ratio, total_debt, ...)
- source_text quotes the covenant clause
- calculation_request names the database fields to use and how to combine them
- Available fields: revenue, ebitda, net_operating_income, cash_balance,
  current_assets, current_liabilities, total_debt, debt_service
- Extract every measurable financial covenant; return {"covenants": []} if there are none
"""


async def extract_covenants(document_text: str) -> tuple[list[CovenantRule], InferenceMeta]:
    provider = get_llm_provider()
    raw, meta = await provider.generate(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Extract financial covenants from this loan agreement:\n\n{document_text}",
            },
        ],
        max_tokens=1024,
        json_mode=True,
    )

    payload = extract_json(raw)
    covenants_raw = payload.get("covenants", [])
    if not isinstance(covenants_raw, list):
        raise ValueError("LLM response missing 'covenants' array")

    covenants: list[CovenantRule] = []
    for index, item in enumerate(covenants_raw):
        try:
            covenants.append(CovenantRule.model_validate(item))
        except ValidationError as exc:
            raise ValueError(f"Invalid covenant at index {index}: {exc}") from exc

    return covenants, meta
