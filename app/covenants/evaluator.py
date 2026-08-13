"""Deterministic verdict: the only place actual is compared to threshold."""

from app.covenants.calculation_pipeline import run_calculation
from app.covenants.schemas import (
    ComplianceStatus,
    CovenantOperator,
    CovenantRule,
    EvaluationResult,
)

DEFAULT_WARNING_BUFFER = 0.10


def _evaluate_status(
    actual: float,
    threshold: float,
    operator: CovenantOperator,
    warning_buffer: float,
) -> ComplianceStatus:
    if operator in (">=", ">"):
        if actual < threshold:
            return "breached"
        return "warning" if actual < threshold * (1 + warning_buffer) else "compliant"

    if actual > threshold:
        return "breached"
    return "warning" if actual > threshold * (1 - warning_buffer) else "compliant"


def evaluate_actual(
    rule: CovenantRule,
    actual: float,
    inputs: dict[str, float],
    warning_buffer: float = DEFAULT_WARNING_BUFFER,
) -> EvaluationResult:
    """Compare a pre-computed actual value against the covenant threshold."""
    return EvaluationResult(
        name=rule.name,
        metric=rule.metric,
        source_text=rule.source_text,
        operator=rule.operator,
        threshold=rule.threshold,
        actual=round(actual, 4),
        status=_evaluate_status(actual, rule.threshold, rule.operator, warning_buffer),
        inputs=inputs,
        currency=rule.currency,
        difference=round(actual - rule.threshold, 4),
    )


def undetermined(
    rule: CovenantRule,
    status: ComplianceStatus,
    reason: str | None,
    inputs: dict[str, float] | None = None,
) -> EvaluationResult:
    """Result for covenants that could not be measured — never a guessed verdict."""
    return EvaluationResult(
        name=rule.name,
        metric=rule.metric,
        source_text=rule.source_text,
        operator=rule.operator,
        threshold=rule.threshold,
        actual=None,
        status=status,
        inputs=inputs or {},
        currency=rule.currency,
        reason=reason,
    )


async def evaluate(
    rule: CovenantRule,
    data: dict[str, float],
    warning_buffer: float = DEFAULT_WARNING_BUFFER,
) -> EvaluationResult:
    """
    Full Pipeline 2: LLM calculation → deterministic verdict.
    """
    calc = await run_calculation(rule, data)

    if calc.actual is None:
        status: ComplianceStatus = "insufficient_data" if not calc.inputs else "manual_review"
        return undetermined(rule, status, calc.error, calc.inputs)

    return evaluate_actual(rule, calc.actual, calc.inputs, warning_buffer)
