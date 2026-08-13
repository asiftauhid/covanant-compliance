"""Coercion helpers for values coming from SQL rows and LLM JSON."""

from decimal import Decimal, InvalidOperation


def to_float(value: object) -> float | None:
    """Return value as a float, or None if it is not a number (dates, text, bools)."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            return float(value)
        except (ValueError, OverflowError, InvalidOperation):
            return None
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def numeric_map(raw: object) -> dict[str, float]:
    """Keep only the numeric entries of a mapping, keyed by string names."""
    if not isinstance(raw, dict):
        return {}
    return {
        str(key): number
        for key, value in raw.items()
        if (number := to_float(value)) is not None
    }
