# Covenant Compliance Monitor

AI-powered loan covenant compliance system for portfolio monitoring. Upload a loan agreement PDF and the system extracts its financial covenants, queries borrower data from PostgreSQL, computes each covenant value, and returns a deterministic compliance verdict with the SQL, inputs, and formula behind it.

Built for the **Orbii AI Product Engineer** portfolio brief: the LLM handles the open-ended work — extraction, SQL, and choosing the formula — while Python computes the number and compares it to the threshold.

## Architecture

```
Loan PDF
  → LLM extracts covenants        (Pipeline 0)
  → LLM writes SQL, guardrails check it   (Pipeline 1)
  → PostgreSQL rows
  → LLM returns a formula, Python evaluates it  (Pipeline 2)
  → Python evaluator: compliant / warning / breached
```

| Layer | Responsibility |
|-------|----------------|
| **LLM (OpenAI or Ollama)** | Covenant extraction, SQL generation, choosing the formula |
| **FastAPI** | Orchestration, guardrails, verified arithmetic, audit responses |
| **PostgreSQL (Neon)** | Borrower financial snapshots |
| **Next.js** | Demo UI for upload + results |

Anything the system cannot verify returns `insufficient_data` or `manual_review` with a reason — never a silent guess.

## Project structure

```
covenant-compliance/
├── app/
│   ├── ai/                 # Provider switch, prompts, JSON + formula parsing
│   ├── chatwithdata/       # NL Q&A over borrower tables
│   ├── covenants/          # Pipelines, evaluator, domain schemas
│   ├── database/           # Models, session, SQL guardrails, schema prompt
│   ├── documents/          # PDF text extraction
│   └── main.py             # FastAPI endpoints
├── frontend/
│   ├── app/                # Next.js routes, fonts, base styles
│   ├── components/         # Workspace, data browser, covenant + chat panels
│   │   └── chatwithdata/   # Chat with data UI
│   └── lib/                # API client + shared types
├── scripts/                # Seed data, pipeline tests, sample PDF generator
└── samples/                # Sample loan agreement PDF
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Neon PostgreSQL database (or any Postgres)
- An OpenAI API key (default provider, `gpt-4o-mini`), or
  [Ollama](https://ollama.com/) + `qwen2.5:3b` to run entirely offline

## Quick start

### 1. Backend

```bash
cd covenant-compliance
python -m venv .covenat_monitor
source .covenat_monitor/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Set DATABASE_URL and OPENAI_API_KEY

# To run without any API key instead, set LLM_PROVIDER=ollama and:
# ollama pull qwen2.5:3b

python scripts/seed_database.py
python scripts/create_sample_pdf.py
python -m uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Demo UI: http://localhost:3000

The window is a two-pane workspace: the database tables on the left, and on the
right either **Covenant check** or **Chat with data**, with a divider you can
drag between them
(double-click to reset). Below 900px the panes stack.

Upload `samples/loan_agreement_sample.pdf`, pick **borrower_001**, period
**2026-07**, and run the check. DSCR comes back **breached** (1.18 vs 1.25).
Each result expands into an audit trail: the clause, the inputs used, and the
SQL that fetched them.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | API + LLM config |
| GET | `/borrowers` | Borrower list for the UI selector |
| GET | `/tables` | Readable tables with row counts |
| GET | `/tables/{name}` | Rows from one table (same whitelist as the guardrails) |
| POST | `/covenants/extract` | PDF → covenant rules |
| POST | `/covenants/analyze` | PDF + borrower + period → full analysis |
| POST | `/covenants/check` | Single covenant + retrieval intent |
| POST | `/data/retrieve` | Pipeline 1 only (NL → SQL → rows) |
| POST | `/chatwithdata` | Ask a question over borrower data |

## Test scripts

```bash
python scripts/test_llm.py         # provider reachability
python scripts/test_pipeline1.py   # SQL retrieval
python scripts/test_pipeline2.py   # calculation + evaluation
```

## Environment variables

**Backend (`.env`)**

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | Neon/Postgres connection string |
| `LLM_PROVIDER` | `openai` | `openai` or `ollama` |
| `OPENAI_API_KEY` | — | Required when `LLM_PROVIDER=openai` |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI chat model |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API base URL |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API (when `LLM_PROVIDER=ollama`) |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Local model |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated frontend origins |

Switching providers is a single env var; every pipeline goes through the same
provider interface.

**Frontend (`.env.local`)**

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI base URL |

## Design notes

**Trust boundary.** The LLM decides *what* to measure and *how*; Python decides
the verdict. Nothing a model asserts is taken at face value:

- Generated SQL must pass guardrails — SELECT only, whitelisted tables
  (`borrowers`, `financial_snapshots`), JOINs and aggregates allowed when needed,
  no `UNION` / writes, and an enforced `LIMIT 100`
- The calculation step returns a formula, which is re-evaluated in Python
  against the values the database returned. Models state the formula more
  reliably than they do the arithmetic, and one test run had a model report
  `1.2636` for `280000 / 225000`
- A formula may only reference retrieved columns, and only `+ - * / ** ()` are
  evaluated, so an invented input or any code-like expression fails instead of running
- If a model echoes back numbers that do not match the database, the result is
  rejected rather than reported
- Comparison lives solely in `evaluator.py`: `compliant` / `warning` /
  `breached` with a 10% warning buffer
- Anything unresolved becomes `insufficient_data` or `manual_review` with a
  reason, never a guessed verdict

**Performance.** Covenants are checked concurrently with `asyncio.gather`, each
on its own SQLAlchemy session, so wall time tracks the slowest covenant rather
than their sum. LLM calls share one keep-alive HTTP client and request JSON mode
(`response_format` on OpenAI, `format` on Ollama), which makes replies parse on
the first try and keeps the retry path rare. A three-covenant analysis of the
sample PDF runs in roughly 9-13s end to end on `gpt-4o-mini`.

**Resilience.** Each covenant check is isolated: a failure degrades that one
result instead of the whole request. Failed queries roll back so a later check
on the same connection is unaffected, and the engine uses `pool_pre_ping` for
Neon's idle connection drops.

**Deployment.** API + DB run on Render/Neon with `LLM_PROVIDER=openai`; no
inference server to host. Set `LLM_PROVIDER=ollama` to run the whole stack
locally with no third-party API.

### Deploy for free

You already have Neon. Use **Render** (API, free web service) and **Vercel**
(Next.js UI, free). First request after idle can take ~1 minute while Render
wakes up.

**1. Push this repo to GitHub** (if it is not already up to date).

**2. API on Render**

1. Go to [render.com/new/blueprint](https://render.com/new/blueprint) and
   connect `covanant-compliance`.
2. Apply `render.yaml`. Choose the **Free** instance.
3. Set these environment variables:

| Variable | Value |
|----------|--------|
| `DATABASE_URL` | your Neon connection string |
| `OPENAI_API_KEY` | your OpenAI key |
| `CORS_ORIGINS` | `https://YOUR-APP.vercel.app` (add after step 3) |

4. Copy the API URL, e.g. `https://covenant-compliance-api.onrender.com`.

**3. UI on Vercel**

1. Import the same GitHub repo at [vercel.com/new](https://vercel.com/new).
2. Set **Root Directory** to `frontend`.
3. Add `NEXT_PUBLIC_API_URL` = the Render URL (no trailing slash).
4. Deploy. Then paste the Vercel URL into Render `CORS_ORIGINS` and redeploy
   the API (Vercel `*.vercel.app` hosts are also allowed by default).

Open the Vercel URL. The first covenant check may be slow while Render spins up.

## Sample data

10 UAE-style borrowers with July 2026 snapshots, seeded to produce a mix of
verdicts against the sample agreement:

| Borrower | DSCR (≥ 1.25) | Current ratio (≥ 1.20) | Total debt (≤ 750k) |
|----------|---------------|------------------------|---------------------|
| `borrower_001` | 1.18 breached | 1.2444 warning | 610,000 compliant |
| `borrower_002` | 2.7368 compliant | 1.6774 compliant | 480,000 compliant |
| `borrower_010` | 0.8696 breached | 1.1304 breached | 780,000 breached |

## License

MIT
