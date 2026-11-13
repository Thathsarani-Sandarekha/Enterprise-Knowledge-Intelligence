<div align="center">

<img src="docs/assets/asteria-cover.svg" width="100%" alt="Asteria Studio — Enterprise Knowledge Intelligence Platform" />

# Asteria Studio

### Enterprise Knowledge Intelligence for Hospitality Design

**A permission-aware, evidence-grounded document intelligence platform for architecture and interior-design workflows.**

Bring architectural specifications, supplier schedules, material approvals, and project decisions into one searchable workspace—without separating an answer from its source evidence.

[**Explore the architecture**](#system-architecture) · [**See the application workflow**](#application-walkthrough) · [**Review evaluations**](#evaluation--engineering-evidence) · [**Run locally**](#getting-started) · [**Demo script**](docs/DEMO_SCRIPT.md)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=flat-square&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-TypeScript-111827?style=flat-square&logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM%20inference-F55036?style=flat-square)
![AWS](https://img.shields.io/badge/AWS-S3%20adapter-FF9900?style=flat-square&logo=amazons3&logoColor=white)

</div>

---

## Executive overview

Asteria Studio is an end-to-end **Retrieval-Augmented Generation (RAG)** application designed around a fictional US hospitality architecture and interior-design consultancy. Its teams need to make project decisions using a mix of DOCX approval memos, PDF registers, XLSX supplier schedules, and renovation briefs. The right answer depends on **which project**, **which source version**, and **which team member is allowed to see it**.

The implementation connects document ingestion and structured source metadata to **PostgreSQL full-text search, pgvector semantic search, reciprocal rank fusion (RRF), cross-encoder reranking, and Groq-generated answers with verified source excerpts**. A Next.js workspace exposes document management, natural-language questions, and a citation audit trail. Access predicates are applied to retrieval **before** evidence reaches the LLM.

**Engineering emphasis:** source provenance · tenant/role-aware retrieval · deterministic test surfaces · retrieval benchmarking · local-first reproducibility · optional Amazon S3 storage.

### At a glance

| Capability | Implementation |
|---|---|
| **Document ingestion** | PDF/DOCX via Docling; XLSX via OpenPyXL; background ingestion worker; persistent document status |
| **Search** | PostgreSQL full-text + 384-dimensional local sentence embeddings in pgvector |
| **Ranking** | Reciprocal rank fusion followed by cross-encoder reranking |
| **Answering** | Groq-hosted `openai/gpt-oss-20b`, structured response contract, checked source excerpts |
| **Access scope** | Tenant isolation, document-role grants, admin-only upload/permission management in the local demo |
| **Storage** | Local filesystem by default; Boto3-backed private S3 object storage available as an option |
| **Delivery** | FastAPI, Next.js/TypeScript, Alembic migrations, Dockerfiles/Compose, pytest and GitHub Actions workflows |

## Business context

### The problem

Consider a team renovating guest rooms at **Solstice Grand Resort**. The studio must compare an approved upholstery specification with supplier quotations and a fire-document register. A designer wants to know which material is approved and what checks remain outstanding; procurement needs the price and lead time; a project manager needs to understand whether the specification can be released for ordering.

These facts are spread across file formats and departments. A plain keyword search does not synthesize the evidence. A general LLM prompt cannot guarantee which documents were consulted, and a single shared chat history is the wrong access boundary for restricted commercial records.

### Target users and decisions

| User | Typical decision | Information scope in the demo |
|---|---|---|
| **Studio administrator** | Upload specifications, assign permitted roles, review project files | Tenant-wide document administration |
| **Interior designer** | Confirm approved materials, finishes, and conditions | Design-authorized documents |
| **Procurement specialist** | Compare supplier bids, prices, and lead times | Procurement-authorized documents |
| **Project manager** | Identify unresolved approval dependencies and project actions | Project-authorized documents |
| **Separate tenant** | Work within another fictional firm's records | Its own tenant only |

The included hospitality samples are synthetic, allowing the workflow and access boundaries to be reproduced without relying on confidential project material.

## Application capabilities

- **Document library:** upload PDF, DOCX, and XLSX files; validate supported formats and size; detect duplicates by SHA-256; monitor queued/processing/ready/failed states.
- **Structured ingestion:** parse documents, create source-aware chunks, embed locally, and index them for lexical and vector retrieval.
- **Permission-aware discovery:** apply tenant and document-grant filters in both retrieval branches rather than filtering an already-retrieved set inside the UI.
- **Hybrid search:** recover exact project IDs and SKU terms through lexical search while also retrieving semantically related passages; fuse and rerank candidate lists.
- **Grounded knowledge assistant:** produce concise project answers with inspectable document names, source locations, and verified supporting excerpts; abstain when evidence cannot support a response.
- **Role demonstration:** switch between fictional studio roles to inspect how identical queries behave under different document grants.
- **Pluggable original-file storage:** preserve local references and optionally store newly uploaded original files in private S3 using Boto3, with a temporary local copy during parsing.

## Application walkthrough

> **Video:** [3–5 minute presentation storyboard](docs/DEMO_SCRIPT.md) · **Recording:** add the published video URL here after recording.
>
> **Screenshots:** capture the running application using the guide in [`docs/assets/screenshots/README.md`](docs/assets/screenshots/README.md). The image paths below are intentionally reserved rather than filled with fabricated UI images.

| Scene | What viewers see | What it proves |
|---|---|---|
| **01 · Document Library** | Studio Administrator uploads a synthetic renovation brief and watches it reach **Ready** | Upload validation, persistent queue, parsing, embedding and indexing |
| **02 · Project question** | “What could delay the guestroom seating renovation at Solstice Grand Resort?” | Cross-section retrieval and a business-relevant answer |
| **03 · Source audit** | The user expands the grouped source document to inspect its verified supporting excerpts | Provenance, traceability and human review |
| **04 · Access comparison** | Interior Designer cannot retrieve restricted supplier prices; Procurement Specialist receives a quoted price and lead time | Backend document-grant and tenant-filtered retrieval |

**Observed local demo:** the renovation-brief answer cited five verified excerpts from one source document; a procurement query returned **USD 145/yard** and a **21-day quoted lead time** for `UPH-FR-220`, while the designer view did not disclose that restricted quotation. These are scenario observations, not benchmark accuracy scores.

<!-- Once captured, uncomment and commit real application screenshots:
![Document library](docs/assets/screenshots/document-library.png)
![Knowledge assistant and grouped citations](docs/assets/screenshots/knowledge-answer.png)
![Role-based access comparison](docs/assets/screenshots/role-comparison.png)
-->

## System architecture

### A. Implemented system — local-first with optional S3

<p align="center">
  <img src="docs/assets/architecture-implemented.svg" width="100%" alt="Implemented Asteria system: Next.js, FastAPI, local or S3 storage, worker ingestion, PostgreSQL pgvector, hybrid retrieval, reranking and Groq answers" />
</p>

[Editable Mermaid diagram](docs/diagrams/implemented-architecture.mmd) · [Full architecture notes](docs/ARCHITECTURE.md)

The implemented system separates **interactive requests**, **durable ingestion**, **indexed data**, and **answer generation**. The storage interface supports local files and S3 without changing the document parser or search stack.

#### Ingestion: from an uploaded file to a searchable record

1. **Upload and validate.** FastAPI checks file type/size, deduplicates using a document hash, records tenant and role grants, and creates a queued document record.
2. **Persist the original.** A storage adapter writes the bytes to local disk by default, or to a tenant-prefixed private S3 object when enabled.
3. **Claim work durably.** The Python worker claims queued database records using row locking; status changes survive an API process restart.
4. **Extract and chunk.** Docling processes DOCX/PDF; OpenPyXL extracts spreadsheet cells and row-range metadata. Source coordinates are retained for auditability.
5. **Embed and index.** Sentence Transformers generates 384-dimensional vectors stored alongside chunks in PostgreSQL/pgvector. SQL text indexes support lexical retrieval.

#### Query: from a question to cited evidence

1. Next.js sends a question through its server-side API gateway to FastAPI.
2. The backend resolves the selected **local demo principal** and applies tenant/role predicates to eligible documents in SQL.
3. Keyword and vector retrieval generate candidate passages; **RRF** merges the ranks; a **cross-encoder** reranks them.
4. Authorized evidence and the question are passed to a Groq-hosted LLM with a structured response contract.
5. The backend checks citation evidence references and source quotations before returning the answer. The frontend groups multiple excerpts under their source document.

> **Trust boundary:** The role selector is an intentional *local identity simulator* used to exercise real backend document-grant logic. Production login/token verification is shown only in the reference design below.

### B. Production reference architecture — proposed AWS deployment

<p align="center">
  <img src="docs/assets/architecture-aws-reference.svg" width="100%" alt="Proposed AWS architecture: CloudFront, ECS Fargate, ECR, API Gateway, internal load balancer, RDS PostgreSQL, private S3 and CloudWatch" />
</p>

[Editable Mermaid diagram](docs/diagrams/aws-reference-architecture.mmd)

This is a **deployment design**, not a description of deployed cloud infrastructure. Its purpose is to show where the existing components would run and which operating capabilities would be supplied by managed AWS services.

| Reference component | Responsibility |
|---|---|
| **CloudFront / public ALB** | HTTPS entry and delivery path for container-hosted Next.js |
| **ECS Fargate** | Independently run the Next.js web service, FastAPI API, and ingestion worker |
| **ECR** | Store versioned application container images |
| **API Gateway + VPC Link + internal ALB** | Controlled ingress into private API containers |
| **RDS PostgreSQL + pgvector** | Persist metadata, permissions, chunks, keyword and vector indexes |
| **Private S3 bucket** | Persist original documents; the Boto3 storage adapter is included in the current code |
| **Secrets Manager / IAM task roles** | Managed credentials and narrowly scoped service permissions |
| **CloudWatch** | Centralized container logs, operational metrics, and alerting |
| **Enterprise OIDC / Cognito** | Verified user identity feeding the existing authorization model |

**Current implementation boundary:** Boto3 integration and container build definitions are in the repository; a successful live S3 round-trip, full Compose deployment, and AWS infrastructure provisioning are separate verification/deployment steps.

## Engineering decisions

| Decision | Why it exists | Engineering consequence |
|---|---|---|
| **PostgreSQL + pgvector** | Keep metadata, permission joins, full-text indexes and vector similarity within a single transactional data layer | Fewer moving services for a local-first demo; SQL predicates protect the retrieval boundary |
| **Lexical + vector retrieval** | Project codes, SKU IDs and exact numbers coexist with natural-language questions | Both exact-term and semantic retrieval are available; actual effectiveness is measured separately |
| **RRF + cross-encoder** | Combine rankings without requiring comparable score scales, then improve passage ordering | Higher compute/latency than keyword-only search; not assumed superior in every corpus |
| **Database-backed worker** | Document parsing and embedding are heavier than a web request | Durable queued/processing/ready/failed states and independent worker execution |
| **Source-aware chunks** | Answers need auditable evidence, including spreadsheet locations | The UI can expose document names, sections, sheets and cell ranges |
| **Backend citation checking** | Model-formatted quotations may drift from retrieved text | Rejects unsupported citation references/quotes; does not substitute for human semantic faithfulness review |
| **Authorization before LLM** | Restricted supplier records must not enter a model prompt for unauthorized roles | Tenant and document grants constrain both lexical and vector search branches |
| **Local storage + S3 adapter** | Preserve an offline development path while demonstrating a realistic external storage integration | No S3 requirement for local execution; AWS credentials remain server-side |

## Technology stack

| Layer | Technologies |
|---|---|
| **Frontend and gateway** | Next.js 16 / React / TypeScript / Lucide UI components |
| **Backend API** | Python 3.12, FastAPI, Pydantic, SQLAlchemy |
| **Document processing** | Docling, OpenPyXL, Python ingestion worker |
| **Embeddings and reranking** | Sentence Transformers `all-MiniLM-L6-v2`, `ms-marco-MiniLM-L-6-v2` cross-encoder |
| **Search and persistence** | PostgreSQL 17, pgvector, SQL full-text search, RRF |
| **LLM** | Groq API, `openai/gpt-oss-20b`, JSON-structured answer handling |
| **Storage** | Local filesystem, optional Amazon S3 via Boto3 |
| **Packaging** | Conda, Alembic, Docker, Docker Compose |
| **Testing / evaluation** | pytest, retrieval/answer/security evaluation scripts, GitHub Actions |

## Evaluation & engineering evidence

The repository includes evaluation cases, scripts, per-case results and methodological notes in [`backend/evaluation/`](backend/evaluation/) and [`docs/EVALUATION.md`](docs/EVALUATION.md). **The retrieval benchmark was run on three indexed synthetic documents and 15 queries (12 answerable, 3 access/empty-result probes), before the later additional demo document.** Results are document-level at `K=5`.

### Retrieval quality and latency

| Strategy | Document Recall@5 | MRR@5 | Warm p50 | Warm p95 |
|---|---:|---:|---:|---:|
| **Keyword (PostgreSQL full-text)** | 1.000 | **0.889** | **3.6 ms** | 22.5 ms |
| **Vector (pgvector)** | 1.000 | 0.635 | 10.8 ms | 12.9 ms |
| **Hybrid + RRF + rerank** | 1.000 | 0.833 | 115.4 ms | 265.1 ms |

**Interpretation:** All methods retrieved a relevant document within five positions in this tiny corpus. Hybrid retrieval did **not** outperform keyword search on MRR in this pilot; the ranking/latency trade-off is part of the engineering evaluation, not hidden by the architecture diagram.

### Answer generation and access checks

| Signal | Observed outcome | Scope |
|---|---|---|
| **Automated answer rules** | **10 / 15 passed (66.67%)** | Original three-document B3 pilot; includes one API error |
| **Full answer API latency** | p50 **3.867 s**, p95 **16.689 s** | Original B3 run, model/provider dependent |
| **Forbidden source exposures** | **0 observed** | Tested pilot queries and simulated identity scopes |
| **Backend regression suite** | **37 passed, 1 skipped** | Latest reported local run, including four S3 adapter tests |
| **Manual claim-level faithfulness** | Not yet scored | Requires reviewer judgments beyond exact-quote matching |

The answer-quality pilot exposed citation-format mismatches and intermittent provider timeouts. Later interactive demo questions produced successful cited answers, but those observations do not replace a full rerun of the answer benchmark. See [evaluation details](docs/EVALUATION.md) and the [raw retrieval](backend/evaluation/results/retrieval_pilot.json) / [answer](backend/evaluation/results/answer_quality_pilot.json) reports.

### Reproduce the checks

From an activated backend environment:

```cmd
cd backend
python -m pytest -q
python -m pytest -q tests\test_s3_storage_adapter.py
```

With PostgreSQL running, the sample documents indexed and the required model resources available:

```cmd
python scripts\evaluate_retrieval.py
python scripts\evaluate_security.py
python scripts\evaluate_answers.py
```

The answer evaluation calls Groq; account access and provider availability affect execution. Scripts write pilot JSON/Markdown results under `backend/evaluation/results/`.

## Getting started

### Prerequisites

- Windows 10/11 with **Conda**, Python 3.12 and Node.js 24 (the project has been tested with this local setup).
- Docker Desktop for the PostgreSQL/pgvector database.
- Groq API credentials for answer generation; retrieval can be evaluated independently.
- Optional: an authorized private S3 bucket and Boto3 credentials for live storage tests.

### 1 · Clone and configure the backend

```cmd
git clone https://github.com/YOUR_USERNAME/enterprise-knowledge-intelligence.git
cd enterprise-knowledge-intelligence
conda create -n docmind_env python=3.12 -y
conda activate docmind_env
cd backend
python -m pip install -r requirements.txt
python -m pip install -r requirements.txt
```

Create **`backend/.env`** with your own values (do not commit this file):

```dotenv
APP_MODE=local
DEV_API_KEY=replace_with_a_long_random_local_value
DATABASE_URL=postgresql+psycopg://eki:local_only_password@localhost:5433/eki
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
STORAGE_BACKEND=local
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

The requirements files are maintained under `backend/`; if you consolidate dependency manifests, update the commands, Dockerfile and CI workflows together.

### 2 · Start the database and apply migrations

From the project root:

```cmd
cd ..
docker compose up -d db
cd backend
python -m alembic upgrade head
```

### 3 · Start the API and ingestion worker

**Terminal A — API** (inside `backend`, with Conda active):

```cmd
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal B — worker** (new terminal):

```cmd
conda activate docmind_env
cd backend
python -m app.worker
```

Open `http://127.0.0.1:8000/health` for health status or `http://127.0.0.1:8000/docs` for interactive FastAPI documentation.

### 4 · Start the frontend

**Terminal C** (from the project root):

```cmd
cd frontend
npm ci
```

Create **`frontend/.env.local`** with the same local development key:

```dotenv
BACKEND_API_URL=http://127.0.0.1:8000
DEV_API_KEY=replace_with_a_long_random_local_value
```

Then run:

```cmd
npm run dev
```

Visit **http://localhost:3000**. Select **Studio Administrator**, upload the files under [`samples/hospitality/`](samples/hospitality/), and verify each document reaches **Ready**. The role selector can then demonstrate access-scoped answers.

### Optional · Amazon S3 original-document storage

Keep local storage for offline development. To use S3 for **new** documents, set `STORAGE_BACKEND=s3`, `AWS_S3_BUCKET`, `AWS_REGION`, and `S3_KEY_PREFIX` in `backend/.env`. Provide AWS credentials through the standard Boto3 credential chain (such as an AWS profile). The worker uses temporary local files to pass S3 originals to Docling.

```cmd
cd backend
python -m pytest -q tests\test_s3_storage_adapter.py
python -m scripts.s3_storage_smoke
```

The second command performs a real bucket round-trip and requires AWS access; follow [`docs/S3_SETUP.md`](docs/S3_SETUP.md) before running it. Returning to `STORAGE_BACKEND=local` leaves existing S3 references readable if bucket access remains configured.

### Optional · Full Docker Compose profile

The base [`docker-compose.yml`](docker-compose.yml) runs PostgreSQL. The overlay adds the API, frontend, and worker:

```cmd
docker compose -f docker-compose.yml -f compose.demo.yml config --quiet
docker compose -f docker-compose.yml -f compose.demo.yml up --build -d
docker compose -f docker-compose.yml -f compose.demo.yml ps
```

Ensure `backend/.env` and `frontend/.env.local` are configured first. Local Docker image pulls previously experienced registry TLS timeouts, so a complete end-to-end container run should be checked before describing the Compose stack as verified.

## API overview

The frontend talks through a server-side gateway at `/api/gateway/[...path]`. The backend exposes versioned routes:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/documents` | Upload and queue a validated document (demo admin) |
| `GET` | `/api/v1/documents` | List accessible documents |
| `GET` | `/api/v1/documents/{id}` | Read authorized document metadata |
| `PUT` | `/api/v1/documents/{id}/permissions` | Update document grants (demo admin) |
| `POST` | `/api/v1/knowledge/search` | Retrieve permission-filtered, reranked evidence |
| `POST` | `/api/v1/knowledge/ask` | Answer with source citations |
| `POST` | `/api/v1/search/vector` | Vector-only diagnostic search |

Example request body for `/api/v1/knowledge/ask`:

```json
{
  "question": "Which upholstery is approved for Solstice Grand Resort and what checks remain before ordering?",
  "project_code": "SGR-2025",
  "top_k": 5
}
```

In local mode, direct backend requests require `x-api-key` and the selected `x-demo-user`. The Next.js gateway keeps the development key server-side. These simulator headers are a development interface; real deployment would resolve principals from verified identity claims.

## Repository structure

```text
enterprise-knowledge-intelligence/
├── .github/workflows/          # Unit, frontend-build and container-build workflows
├── backend/
│   ├── app/
│   │   ├── routes/             # Documents, search, knowledge and principal endpoints
│   │   ├── services/           # Extraction, storage, retrieval, ranking, citation checking
│   │   └── worker.py           # Database-queued ingestion worker
│   ├── evaluation/             # Query sets, scoring code and curated pilot results
│   ├── migrations/             # Alembic document and grant schema
│   ├── scripts/                # Evaluation, smoke and S3 scripts
│   ├── tests/                  # Automated regression, access and storage tests
│   └── Dockerfile
├── frontend/
│   ├── app/                    # Next.js routes and server-side API gateway
│   ├── components/             # Search/chat and document management
│   └── Dockerfile
├── docs/
│   ├── assets/                 # Architecture SVGs and screenshot folder
│   ├── diagrams/               # Editable Mermaid diagram source
│   ├── ARCHITECTURE.md
│   ├── EVALUATION.md
│   ├── PORTFOLIO_CASE_STUDY.md
│   └── DEMO_SCRIPT.md
├── samples/hospitality/        # Synthetic DOCX/PDF/XLSX source material
├── docker-compose.yml          # Local PostgreSQL
└── compose.demo.yml            # API + worker + frontend overlay
```

## Delivery, testing and operational readiness

The repository includes [`ci.yml`](.github/workflows/ci.yml), [`s3-storage-tests.yml`](.github/workflows/s3-storage-tests.yml), and [`container-build.yml`](.github/workflows/container-build.yml) for backend checks, frontend type/build validation, mocked S3 adapter tests and Docker image builds on GitHub-hosted runners. Their presence is distinct from a confirmed successful remote Actions run.

This is an **inference-oriented LLM application**, not a model-training pipeline. The ML/LLM engineering workflow here is document processing, retrieval/reranking, evaluation, model-call handling, testing and repeatable packaging—not a claimed MLflow experiment-tracking or scheduled retraining system.

**Engineering boundaries and next improvements**

1. **Verified identity:** integrate OIDC/SSO and map signed user claims to tenant/document permissions instead of local role selection.
2. **Grounding evaluation:** add reviewer-graded claim faithfulness and citation support, plus a larger document benchmark and regression gate for known failure cases.
3. **Answer reliability:** reduce unnecessary abstentions and handle model response/citation formatting and timeouts without weakening evidence checks.
4. **Operations:** validate full Compose execution and the live S3 path; add structured metrics, alerting and cloud infrastructure only as deployment needs arise.

## Technical case study and demo

- [**Portfolio case study**](docs/PORTFOLIO_CASE_STUDY.md) — problem framing, architecture choices and engineering trade-offs.
- [**Implementation and AWS reference architecture**](docs/ARCHITECTURE.md) — detailed component boundaries and cloud mapping.
- [**Evaluation report**](docs/EVALUATION.md) — methodology, per-pilot results and interpretation.
- [**Demo script**](docs/DEMO_SCRIPT.md) — business problem → working application → evidence trail → permissions → architecture → measured results.

---

<div align="center">

**ASTERIA / STUDIO**  
*Design knowledge, connected to its evidence.*

</div>
