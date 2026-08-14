import re

_REDACT = (
    re.compile(r"sk-[A-Za-z0-9_\-]+"),
    re.compile(r"Bearer\s+\S+", re.I),
)


def public_error(exc: BaseException) -> str:
    """Exception text safe to show in the UI (secrets stripped)."""
    text = str(exc)
    for pattern in _REDACT:
        text = pattern.sub("[redacted]", text)
    return text
