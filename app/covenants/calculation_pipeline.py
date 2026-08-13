"""
Pipeline 2 — calculation.

The LLM decides how to combine the retrieved values; Python evaluates that
formula against the database values, so no covenant formula is hardcoded here
and no reported number comes from the model's own arithmetic unverified.

  CovenantRule + retrieved data  →  run_calculation()  →  CalculationResult
"""

import math

from app.ai.calculation_generator import generate_calculation
from app.ai.formula_eval import apply_formula
from app.covenants.numeric import numeric_map, to_float
from app.covenants.schemas import CalculationResult, CovenantRule

FinancialData = dict[str, float]

MAX_ATTEMPTS = 2


def _echoed_data_faithfully(claimed: FinancialData, actual_data: FinancialData) -> bool:
    """True when every value the model echoed matches what the database returned."""
    if not claimed:
        return False
    return all(
        name in actual_data and math.isclose(value, actual_data[name], rel_tol=1e-6)
        for name, value in claimed.items()
    )


def _resolve_actual(
    payload: dict, data: FinancialData, *, allow_unverified: bool
) -> tuple[float | None, FinancialData, str | None]:
    """
    Evaluate the model's formula against the database values, never against the
    numbers it echoed back, so a hallucinated input cannot become a verdict.

    With allow_unverified (the final attempt) its own number is accepted as a
    fallback, but only when every value it echoed matches the database.
    """
    formula = payload.get("formula")
    claimed = numeric_map(payload.get("inputs"))
    used = {name: data[name] for name in claimed if name in data} or data
    formula_error: str | None = None

    if isinstance(formula, str) and formula.strip():
        try:
            return round(apply_formula(formula, data), 4), used, None
        except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as exc:
            formula_error = f"Formula evaluation failed: {exc}"

    if payload.get("error"):
        return None, used, str(payload["error"])

    actual = to_float(payload.get("actual"))
    if actual is None:
        return None, used, formula_error or "LLM returned no usable formula or value"
    if not _echoed_data_faithfully(claimed, data):
        return None, used, "LLM reported values that do not match the retrieved data"
    if not allow_unverified:
        return None, used, formula_error or "LLM returned no verifiable formula"

    return round(actual, 4), used, None


async def run_calculation(rule: CovenantRule, data: FinancialData) -> CalculationResult:
    """Compute the covenant actual from retrieved data, retrying once on a bad reply."""
    available = numeric_map(data)
    if not available:
        return CalculationResult(
            metric=rule.metric,
            actual=None,
            inputs={},
            error="No data available for calculation",
        )

    error: str | None = None
    previous = ""

    for attempt in range(MAX_ATTEMPTS):
        fix_context = (previous, error) if attempt and error else None

        try:
            payload, _meta = await generate_calculation(rule, available, fix_context=fix_context)
        except Exception as exc:
            return CalculationResult(
                metric=rule.metric,
                actual=None,
                inputs=available,
                error=f"Calculation failed: {exc}",
            )

        previous = str(payload)
        actual, used, error = _resolve_actual(
            payload, available, allow_unverified=attempt == MAX_ATTEMPTS - 1
        )

        if actual is not None:
            return CalculationResult(metric=rule.metric, actual=actual, inputs=used)

    return CalculationResult(
        metric=rule.metric,
        actual=None,
        inputs=available,
        error=error or "LLM could not compute the covenant value",
    )
