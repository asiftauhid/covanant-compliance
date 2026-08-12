from pydantic import BaseModel


class InferenceMeta(BaseModel):
    model: str
    inference_ms: int
    provider: str
