# Loan Covenant Monitor and Chat With Database

Upload a loan agreement PDF, pick a borrower and month, and see whether each covenant is **compliant**, **warning**, or **breached**. Also ask questions about the borrowers data in plain English.

**Live demo:** [UI](https://covenant-compliance-bice.vercel.app) · [API docs](https://covenant-compliance-api.onrender.com/docs) · [Health](https://covenant-compliance-api.onrender.com/health)

**Stack:** Next.js · FastAPI · PostgreSQL (Neon) · OpenAI or Ollama (For Personal Deployment)

---

## Features

|                    | What it does                                                                                              |
| ------------------ | --------------------------------------------------------------------------------------------------------- |
| **Covenant check** | PDF → extract covenants → construct formula → fetch financial da → compute metrics → status + audit trail |
| **Ask the data**   | Natural-language questions over `borrowers` and `financial_snapshots` data from DB                        |
| **Trust boundary** | LLM proposes structure/SQL/formulas and Python owns guardrails, math, and verdicts                        |

---

## Architecture

```mermaid
%%{init: {"flowchart": {"htmlLabels": false, "nodeSpacing": 24, "rankSpacing": 28}, "themeVariables": {"fontSize": "12px"}}}%%
flowchart LR
  UI["Next.js"]
  API["FastAPI"]
  DB[("Postgres")]
  LLM["OpenAI / Ollama"]

  UI <-->|"REST"| API
  API <-->|"SQL"| DB
  API <-->|"prompts"| LLM

  classDef box fill:#f8fafc,stroke:#94a3b8,color:#0f172a,rx:6,ry:6
  class UI,API,LLM box
```

### Covenant check

```mermaid
%%{init: {"flowchart": {"htmlLabels": false, "nodeSpacing": 18, "rankSpacing": 22}, "themeVariables": {"fontSize": "11px"}}}%%
flowchart LR
  PDF["PDF"] --> P0["Extract<br/>LLM"]
  P0 --> P1["SQL<br/>LLM + guard"]
  P1 --> DB[("DB")]
  DB --> P2["Formula<br/>LLM → Python"]
  P2 --> P3["Verdict<br/>Python"]
  P3 --> OUT["Results"]

  classDef llm fill:#eff6ff,stroke:#60a5fa,color:#1e3a8a
  classDef py fill:#ecfdf5,stroke:#34d399,color:#064e3b
  classDef io fill:#f8fafc,stroke:#94a3b8,color:#0f172a
  class P0,P1,P2 llm
  class P3 py
  class PDF,OUT io
```

The model extracts covenants, drafts SQL, and suggests formulas. Python validates SQL, evaluates the math on real data, and decides the status, so nothing unverified is reported as fact.

For each covenant runs **SQL → formula → verdict** in parallel. Guardrails: `SELECT` only, tables `borrowers` / `financial_snapshots`, `LIMIT 100`.

### Ask the data

```mermaid
%%{init: {"flowchart": {"htmlLabels": false, "nodeSpacing": 18, "rankSpacing": 22}, "themeVariables": {"fontSize": "11px"}}}%%
flowchart LR
  Q["Question"] --> PLAN["Plan<br/>LLM"]
  PLAN --> SQL["SQL<br/>+ review"]
  SQL --> DB[("DB")]
  DB --> ANS["Answer<br/>from rows"]

  classDef llm fill:#eff6ff,stroke:#60a5fa,color:#1e3a8a
  classDef io fill:#f8fafc,stroke:#94a3b8,color:#0f172a
  class PLAN,SQL,ANS llm
  class Q io
```

The planner turns the question into intents and filters. SQL is generated, checked against those filters, then executed. The answer is narrated only from retrieved rows from the DB.

---

## Run locally

**Prerequisites:** Python 3.11+, Node 18+, a Postgres URL (e.g. [Neon](https://neon.tech)), and an OpenAI key (or a local [Ollama](https://ollama.com) model).

### 1. Backend

```bash
python -m venv .covenat_monitor
source .covenat_monitor/bin/activate   # Windows: .covenat_monitor\Scripts\activate

pip install -r requirements.txt
cp .env.example .env                   # set DATABASE_URL and OPENAI_API_KEY

python scripts/seed_database.py
python -m uvicorn app.main:app --reload --port 8000
```

API: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend (new terminal)

```bash
cd frontend
cp .env.local.example .env.local       # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

UI: [http://localhost:3000](http://localhost:3000)

### Try the demo

Use `samples/loan_agreement_sample.pdf` with any borrower and period **`2026-07`**.

---

## Environment

### Backend (`.env`)

| Variable                           | Purpose                                                  |
| ---------------------------------- | -------------------------------------------------------- |
| `DATABASE_URL`                     | Postgres connection string                               |
| `OPENAI_API_KEY`                   | Required when `LLM_PROVIDER=openai`                      |
| `LLM_PROVIDER`                     | `openai` (default) or `ollama` (for personal deployment) |
| `OPENAI_MODEL`                     | Default `gpt-4o-mini`                                    |
| `CORS_ORIGINS`                     | Frontend origin(s), comma-separated                      |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | Used when `LLM_PROVIDER=ollama`                          |

### Frontend (`frontend/.env.local`)

| Variable              | Purpose          |
| --------------------- | ---------------- |
| `NEXT_PUBLIC_API_URL` | FastAPI base URL |

---

## Main API routes

| Method | Path                        | Purpose                                         |
| ------ | --------------------------- | ----------------------------------------------- |
| `POST` | `/covenants/analyze`        | PDF + borrower + period → full compliance check |
| `POST` | `/chatwithdata`             | Question over borrower data                     |
| `GET`  | `/borrowers`                | List borrowers                                  |
| `GET`  | `/tables`, `/tables/{name}` | Browse whitelisted tables                       |
| `GET`  | `/health`                   | Status + LLM provider info                      |

---

## Project layout

```text
app/           FastAPI — covenants, chat, SQL guardrails, LLM providers
frontend/      Next.js UI
scripts/       Seed data + pipeline smoke tests
samples/       Demo loan agreement PDF
alembic/       DB migrations
```
