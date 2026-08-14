from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.providers import get_llm_provider, get_provider_info
from app.ai.providers.http_client import close_client
from app.chatwithdata import ChatMessage, chat_with_data
from app.config import settings
from app.covenants.compliance_pipeline import analyze_loan_agreement, check_compliance
from app.covenants.extraction_pipeline import extract_covenants_from_pdf
from app.covenants.retrieval_pipeline import retrieve_data
from app.covenants.schemas import CovenantRule
from app.database.models import Borrower
from app.database.schema_context import ALLOWED_TABLES, MAX_ROWS
from app.database.session import Base, get_db

PDF_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_client()


app = FastAPI(
    title="Covenant Compliance Monitor",
    description="AI-powered loan covenant compliance API",
    version="0.1.0",
    lifespan=lifespan,
)

cors_kwargs: dict = {
    "allow_origins": [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.cors_origin_regex:
    cors_kwargs["allow_origin_regex"] = settings.cors_origin_regex

app.add_middleware(CORSMiddleware, **cors_kwargs)


async def read_pdf(file: UploadFile) -> bytes:
    if file.content_type not in PDF_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Upload a PDF file")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    return content


class RetrieveRequest(BaseModel):
    intent: str


class CheckRequest(BaseModel):
    covenant: CovenantRule
    intent: str


class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


@app.get("/", include_in_schema=False)
def root():
    """Render's public URL hits /, which is not an API route — send people to the docs."""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok", **get_provider_info()}


@app.get("/llm/test")
async def llm_test():
    """Quick check that the configured LLM provider responds."""
    try:
        provider = get_llm_provider()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        text, meta = await provider.generate(
            [{"role": "user", "content": "Reply with exactly: LLM is working."}],
            max_tokens=32,
        )
    except httpx.HTTPError as exc:
        info = get_provider_info()
        raise HTTPException(
            status_code=502,
            detail=(
                f"LLM provider '{info['llm_provider']}' unreachable at "
                f"{info['endpoint']}: {exc}"
            ),
        ) from exc

    return {
        "text": text,
        "model": meta.model,
        "provider": meta.provider,
        "inference_ms": meta.inference_ms,
    }


@app.get("/borrowers")
def list_borrowers(db: Session = Depends(get_db)):
    rows = db.query(Borrower.id, Borrower.name, Borrower.industry).order_by(Borrower.id).all()
    return [{"id": row.id, "name": row.name, "industry": row.industry} for row in rows]


@app.get("/tables")
def list_tables(db: Session = Depends(get_db)):
    """Readable tables and their row counts, for the data browser."""
    tables = []
    for name in sorted(ALLOWED_TABLES):
        table = Base.metadata.tables[name]
        count = db.execute(select(func.count()).select_from(table)).scalar_one()
        tables.append({"name": name, "row_count": count, "columns": list(table.columns.keys())})
    return tables


@app.get("/tables/{name}")
def read_table(
    name: str,
    limit: int = Query(MAX_ROWS, ge=1, le=MAX_ROWS),
    db: Session = Depends(get_db),
):
    """Rows from one readable table. Same whitelist the SQL guardrails use."""
    if name not in ALLOWED_TABLES:
        raise HTTPException(status_code=404, detail=f"Unknown table '{name}'")

    table = Base.metadata.tables[name]
    statement = select(table).order_by(*table.primary_key.columns).limit(limit)
    rows = db.execute(statement).mappings().all()

    return {
        "table": name,
        "columns": list(table.columns.keys()),
        "rows": [dict(row) for row in rows],
    }


@app.post("/data/retrieve")
async def retrieve_data_endpoint(body: RetrieveRequest, db: Session = Depends(get_db)):
    """Pipeline 1: natural language → LLM SQL → guarded execution."""
    result = await retrieve_data(db, body.intent)
    if result.error:
        raise HTTPException(status_code=422, detail=result.error)
    return result


@app.post("/chatwithdata")
async def chat_with_data_endpoint(body: ChatRequest, db: Session = Depends(get_db)):
    """Ask a question over borrower data: retrieve rows, then answer from them."""
    result = await chat_with_data(db, body.question, body.history)
    if result.error and not result.answer:
        raise HTTPException(status_code=422, detail=result.error)
    return result


@app.post("/covenants/check")
async def check_covenant(body: CheckRequest, db: Session = Depends(get_db)):
    """Retrieve data, calculate the actual via LLM, return the compliance verdict."""
    return await check_compliance(db, body.covenant, body.intent)


@app.post("/covenants/extract")
async def extract_covenant_rules(file: UploadFile = File(...)):
    """Extract structured covenant rules from a loan agreement PDF."""
    result = await extract_covenants_from_pdf(await read_pdf(file))
    if result.error:
        raise HTTPException(status_code=422, detail=result.error)
    return result


@app.post("/covenants/analyze")
async def analyze_covenant_compliance(
    file: UploadFile = File(...),
    borrower_id: str = Form(...),
    period: str = Form("2026-07"),
):
    """Full demo flow: PDF → extract covenants → retrieve → calculate → verdict."""
    result = await analyze_loan_agreement(await read_pdf(file), borrower_id, period)
    if result.extraction.error:
        raise HTTPException(status_code=422, detail=result.extraction.error)
    return result
