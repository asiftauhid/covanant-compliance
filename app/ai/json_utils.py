import json
import re

_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
_CODE_BLOCK = re.compile(r"```(?:sql)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> dict:
    """Parse JSON from LLM output, including ```json code blocks."""
    text = text.strip()

    block = _JSON_BLOCK.search(text)
    if block:
        return json.loads(block.group(1))

    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError("No JSON object found in LLM response")


def extract_sql(text: str) -> str:
    """Parse SQL from LLM output — plain text, ```sql block, or JSON with sql key."""
    text = text.strip()

    try:
        payload = extract_json(text)
        if "sql" in payload:
            return str(payload["sql"]).strip().rstrip(";")
    except (ValueError, json.JSONDecodeError):
        pass

    block = _CODE_BLOCK.search(text)
    if block:
        return block.group(1).strip().rstrip(";")

    if text.upper().startswith("SELECT"):
        return text.rstrip(";")

    raise ValueError("No SQL found in LLM response")
