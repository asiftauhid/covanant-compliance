from app.covenants.calculation_pipeline import run_calculation
from app.schemas.covenant import (
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
        upper_warning = threshold * (1 + warning_buffer)
        if actual < upper_warning:
            return "warning"
        return "compliant"

    if actual > threshold:
        return "breached"
    lower_warning = threshold * (1 - warning_buffer)
    if actual > lower_warning:
        return "warning"
    return "compliant"


def evaluate_actual(
    rule: CovenantRule,
    actual: float,
    inputs: dict[str, float],
    warning_buffer: float = DEFAULT_WARNING_BUFFER,
) -> EvaluationResult:
    """Compare a pre-computed actual value against the covenant threshold."""
    status = _evaluate_status(actual, rule.threshold, rule.operator, warning_buffer)

    return EvaluationResult(
        name=rule.name,
        metric=rule.metric,
        source_text=rule.source_text,
        operator=rule.operator,
        threshold=rule.threshold,
        actual=round(actual, 4),
        status=status,
        inputs=inputs,
        currency=rule.currency,
        difference=round(actual - rule.threshold, 4),
    )


def evaluate(rule: CovenantRule, data: dict[str, float], warning_buffer: float = DEFAULT_WARNING_BUFFER) -> EvaluationResult:
    """
    Full Pipeline 2: calculation → verdict.

    1. run_calculation(covenant, retrieved data) → actual
    2. evaluate_actual(actual vs threshold) → compliant / warning / breached
    """
    calc = run_calculation(rule, data)

    if calc.error or calc.actual is None:
        status: ComplianceStatus = (
            "insufficient_data" if calc.inputs and "Missing" in (calc.error or "") else "manual_review"
        )
        return EvaluationResult(
            name=rule.name,
            metric=rule.metric,
            source_text=rule.source_text,
            operator=rule.operator,
            threshold=rule.threshold,
            actual=None,
            status=status,
            inputs=calc.inputs,
            currency=rule.currency,
            reason=calc.error,
        )

    return evaluate_actual(rule, calc.actual, calc.inputs, warning_buffer)
