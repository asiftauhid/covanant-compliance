from typing import Literal

from pydantic import BaseModel, Field

CovenantOperator = Literal[">=", "<=", ">", "<"]

ComplianceStatus = Literal[
    "compliant",
    "warning",
    "breached",
    "insufficient_data",
    "manual_review",
]


class CovenantRule(BaseModel):
    name: str
    metric: str
    operator: CovenantOperator
    threshold: float
    currency: str | None = None
    frequency: str | None = None
    source_text: str
    calculation_request: str | None = None


class CalculationResult(BaseModel):
    metric: str
    actual: float | None
    inputs: dict[str, float]
    error: str | None = None


class EvaluationResult(BaseModel):
    name: str
    metric: str
    source_text: str
    operator: CovenantOperator
    threshold: float
    actual: float | None
    status: ComplianceStatus
    inputs: dict[str, float] = Field(default_factory=dict)
    currency: str | None = None
    difference: float | None = None
    reason: str | None = None
