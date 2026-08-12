"""
Open-ended calculation pipeline.

Given an extracted covenant and retrieved row data, compute the actual value
the covenant asks for. This will be powered by an LLM (same provider as extraction).

Flow:
  CovenantRule + retrieved data  →  run_calculation()  →  CalculationResult
"""

from app.schemas.covenant import CalculationResult, CovenantRule

FinancialData = dict[str, float]


def run_calculation(rule: CovenantRule, data: FinancialData) -> CalculationResult:
    """
    Compute the covenant actual from retrieved data.

    TODO: Wire LLM here — pass rule.source_text, rule.calculation_request,
    and data; require structured JSON { "actual": float, "inputs": {...} }.

    Until then, returns manual_review so we never silently guess.
    """
    used_inputs = {k: v for k, v in data.items() if v is not None}

    return CalculationResult(
        metric=rule.metric,
        actual=None,
        inputs=used_inputs,
        error="Calculation pipeline pending LLM integration",
    )
