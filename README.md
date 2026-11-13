<div align="center">

<img src="docs/assets/asteria-cover.svg" width="100%" alt="Asteria Studio — Enterprise Knowledge Intelligence Platform" />

# Asteria Studio

### Enterprise Knowledge Intelligence for Hospitality Design

**An evidence-grounded, permission-aware RAG platform for architectural specifications, design approvals, supplier records, and renovation project knowledge.**

Transform fragmented project documents into searchable intelligence, traceable answers, and more confident design and procurement decisions.

[Architecture](#system-architecture) · [Live workflow](#application-walkthrough) · [Engineering](#engineering-implementation) · [Evaluation](#evaluation--results) · [Setup](#getting-started) · [Technical case study](docs/PORTFOLIO_CASE_STUDY.md)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=flat-square&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-TypeScript-111827?style=flat-square&logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM%20Inference-F55036?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS-S3%20%7C%20Boto3-FF9900?style=flat-square&logo=amazons3&logoColor=white)

</div>

---

## Executive overview

**Asteria Studio** is an enterprise-oriented document intelligence application built around a hospitality architecture and interior-design consultancy. Project teams work across architectural briefs, material approval memoranda, fire-documentation registers, and supplier schedules. The information they need is spread across PDF, DOCX, and XLSX files, and access requirements vary between design, project management, and procurement.

The platform brings these records into a unified workspace, combining **Docling-based document ingestion**, **PostgreSQL full-text search**, **pgvector semantic retrieval**, **reciprocal rank fusion**, **cross-encoder reranking**, and **Groq-powered structured answer generation**. A backend citation-verification step attaches supporting source excerpts to generated responses, while tenant and document-grant predicates constrain retrieval before information reaches the LLM.

The result is more than conversational document search: it is a complete **document-to-decision pipeline** with persistent ingestion, controlled retrieval, explainable evidence, testable interfaces, and a business-focused Next.js experience.

| Engineering capability | Implementation |
|---|---|
| **Multi-format document intelligence** | PDF/DOCX extraction with Docling; structured XLSX extraction with OpenPyXL; source-aware chunking |
| **Hybrid search** | PostgreSQL lexical search + 384-dimensional pgvector embeddings; RRF and cross-encoder reranking |
| **Evidence-grounded Q&A** | Groq LLM, structured JSON responses, source excerpt verification, inspectable citations |
| **Permission-aware knowledge access** | Tenant scoping and role/document grants enforced within backend retrieval |
| **Document lifecycle** | SHA-256 duplicate checks, persistent processing states, separate ingestion worker |
| **AWS integration** | Boto3-based Amazon S3 document-storage adapter and configurable storage selection |
| **Engineering delivery** | FastAPI, Next.js, Alembic, Docker Compose, GitHub Actions, pytest, reproducible evaluation scripts |

## Business problem and users

### The scenario

During the guestroom renovation at **Solstice Grand Resort**, the design team must determine which upholstery is approved, which supplier submitted the selected material, what supporting documentation is required, and which decisions must be completed before procurement can release the order.

These answers are distributed across material approvals, project briefs, PDF registers, and commercial spreadsheets. Reviewing each file manually creates avoidable coordination work, especially when a project has many revisions and contributors.

Asteria Studio provides a single, permission-aware knowledge interface for these decisions.

| Role | Example question | Value provided |
|---|---|---|
| **Interior Designer** | Which upholstery is approved, and what design conditions remain? | Locate the selected material and inspect the exact approval language |
| **Project Manager** | What could delay the guestroom renovation? | Consolidate action items and approval dependencies from project documents |
| **Procurement Manager** | What are the quoted material cost and delivery lead time? | Retrieve commercial details from authorized supplier records |
| **Studio Administrator** | Which records are indexed, and how are they shared? | Manage the document library and permitted access scope |

The repository includes a reproducible synthetic hospitality document set for the application walkthrough and evaluation.

## Application walkthrough

The interface is organized around two working areas: a **Document Library** for ingestion and a **Knowledge Assistant** for project-specific search and answers.

| Scene | Application interaction | Engineering capability |
|---|---|---|
| **01 — Manage documents** | Studio Administrator uploads a renovation brief and observes its transition to **Ready** | Validation → queue → parsing → embedding → indexing |
| **02 — Ask a project question** | “What could delay the guestroom seating renovation, and what must be checked before ordering?” | Permission-filtered hybrid retrieval and answer generation |
| **03 — Audit the answer** | Expand one document card to inspect the five supporting excerpts | Source-aware chunking and backend citation verification |
| **04 — Compare access scopes** | Ask for supplier prices as Interior Designer and Procurement Manager | Tenant/document-grant enforcement before LLM context construction |

### Example: evidence-backed renovation decision

In the demonstrated workflow, Asteria Studio identifies the **UPH-FR-220** upholstery specification from **Northstar Contract Textiles** and highlights the required final SKU, sample approval, documentation, and procurement release checks. Its answer links back to the source document sections. The procurement view can additionally retrieve a **USD 145/yard quoted price** and a **21-day lead time** from the supplier schedule.

**Demo:** [3–5 minute presentation script](docs/DEMO_SCRIPT.md) · [Technical portfolio case study](docs/PORTFOLIO_CASE_STUDY.md)

<!-- Add genuine screenshots captured from the running Next.js application and then enable these lines.
![Asteria Studio — Document Library](docs/screenshots/document-library.png)
![Asteria Studio — Knowledge Assistant and grouped source citations](docs/screenshots/knowledge-assistant.png)
![Asteria Studio — Permission-aware document access](docs/screenshots/role-access.png)
-->

## System architecture

### 1. Implemented system architecture

<img src="docs/architecture/implemented-system.svg" width="100%" alt="Asteria Studio implemented architecture showing Next.js, FastAPI, document processing, Amazon S3 adapter, PostgreSQL/pgvector, hybrid RAG, Groq, and citation verification" />

The application separates its responsibilities into three key flows:

- **Experience and API:** Next.js provides document management, role-context selection, knowledge search, and grouped evidence cards. The server-side gateway forwards requests to FastAPI.
- **Document intelligence:** FastAPI validates and registers files; the worker parses, chunks, embeds, and indexes documents, preserving project and source metadata throughout processing.
- **Knowledge retrieval and generation:** scoped keyword and vector searches feed RRF and reranking; Groq synthesizes an answer from authorized evidence; the backend validates citation references and text before the frontend displays the result.

### 2. End-to-end RAG workflow

<img src="docs/architecture/rag-workflow.svg" width="100%" alt="Asteria document ingestion, hybrid retrieval, reranking, and grounded answer workflow" />

**Ingestion path**

1. **Upload:** FastAPI validates supported file types and sizes, calculates a document fingerprint, stores document metadata, and assigns its access scope.
2. **Store:** The storage service persists the original document through its configured provider, including **Amazon S3 via Boto3**.
3. **Process:** A Python worker claims queued database records; Docling extracts PDF/DOCX content and OpenPyXL processes XLSX data.
4. **Structure:** Extracted content is chunked with source references such as filename, document section, sheet, and cell range.
5. **Index:** Sentence Transformers generates embeddings; PostgreSQL stores text, metadata, access grants, and pgvector embeddings.

**Knowledge-query path**

1. FastAPI receives a question and determines the request's permitted document scope.
2. **Lexical search** matches precise terms such as project IDs, material codes, and supplier names.
3. **Vector search** finds semantically related passages. Both retrieval branches respect database access predicates.
4. **Reciprocal Rank Fusion** merges ranked candidates; a **cross-encoder** reranks the selected evidence.
5. Groq generates an answer from the retrieved context under a structured output contract.
6. Backend citation checks resolve the evidence to its source. Next.js groups multiple supporting excerpts under each document.

### 3. Enterprise AWS production reference architecture

<img src="docs/architecture/aws-production-reference.svg" width="100%" alt="Asteria Studio AWS production reference with S3, ECS Fargate, ECR, RDS PostgreSQL, API Gateway, Cognito, CloudWatch and private networking" />

This **production reference design** maps the application services to managed cloud capabilities while retaining the existing FastAPI, Next.js, worker, and RAG architecture.

| AWS service | Architecture responsibility |
|---|---|
| **Amazon S3** | Document-object storage accessed by the Boto3 integration |
| **Amazon ECR** | Versioned Docker image registry for application services |
| **Amazon ECS on Fargate** | Independently operated frontend, API, and ingestion-worker workloads |
| **Amazon RDS for PostgreSQL** | Managed relational persistence with pgvector-compatible indexing strategy |
| **Amazon API Gateway + VPC Link / internal ALB** | API ingress and private container-service integration |
| **Amazon Cognito / enterprise OIDC** | Verified identity claims mapped to tenant and role authorization |
| **IAM + AWS Secrets Manager** | Least-privilege service permissions and managed secrets |
| **Amazon CloudWatch** | Centralized logs, operational metrics, alerting, and application diagnostics |
| **Amazon CloudFront / application load balancer** | HTTPS web entry and delivery path |

The **implemented application architecture** above documents the executable code. The **AWS production reference** documents the intended managed-service deployment topology. Both diagrams are supplied as editable SVGs with PNG exports and a Python diagram-rendering source in [`docs/architecture/`](docs/architecture/).

## Engineering implementation

### Source-aware document ingestion

The document pipeline is built for heterogeneous project records rather than uniform plain text. Docling extracts layout-aware PDF and DOCX content, while spreadsheet extraction retains sheet/cell context so a retrieved supplier quote can be traced to its original table. A database-backed worker manages processing state separately from the HTTP request lifecycle.

**Design rationale:** preserve provenance through extraction and make expensive parsing and embeddings independently executable and retryable.

### Hybrid retrieval and reranking

- **PostgreSQL full-text search** supports exact-match queries for technical identifiers and contract terminology.
- **Sentence Transformer embeddings and pgvector** support semantic queries such as “What needs approval before we can order?”
- **RRF** combines rankings from both retrieval strategies without assuming their raw relevance scores are comparable.
- **Cross-encoder reranking** scores the final candidate passages against the full question.

**Design rationale:** architecture and procurement documents mix machine-like identifiers with human-written requirements; both retrieval modes are useful, and evaluation determines their relative value for each corpus.

### Grounded generation and citation audit

Groq provides structured LLM inference. The application preserves evidence IDs and source locations, checks citation excerpts against retrieved chunks, and returns document-level provenance to the interface. The frontend presents concise source cards with expandable quotations rather than repeating a full document card for every excerpt.

**Design rationale:** users must be able to inspect the project records behind a design or procurement recommendation. Literal quotation verification is combined with separately evaluated answer quality.

### Permissions and security boundaries

Tenant IDs and document-role grants constrain retrieval inside the backend and database, so a role's inaccessible supplier documents are excluded before building the LLM context. The application also treats retrieved document content as untrusted input and includes prompt-injection/security test cases and a PII-redaction utility.

The demo role selector exercises this authorization logic with predefined principals. The AWS reference diagram includes an enterprise OIDC/Cognito identity layer for an organization-wide deployment.

### AWS document storage

`backend/app/services/object_storage.py` supplies a Boto3-based S3 adapter with tenant-scoped object keys. Document ingestion references the stored original and materializes it for parsing when needed. Credentials remain in server-side configuration and use the standard AWS credential chain. The storage provider is selected through environment configuration, keeping the document-processing and retrieval code independent of the object-storage service.

### Packaging, CI, and evaluation

- **Docker/Compose:** defined containers for PostgreSQL, FastAPI, the ingestion worker, and Next.js, with a Compose overlay for the complete application.
- **GitHub Actions:** workflows for Python tests, frontend type/build checks, S3 adapter unit tests, and container builds.
- **PostgreSQL migrations:** Alembic versions preserve schema evolution for document metadata, chunks, and grants.
- **LLMOps/evaluation:** committed question sets, comparison baselines, timing measurements, answer contract checks, and access-security scenarios.

## Technology stack

| Responsibility | Technologies |
|---|---|
| **Application experience** | Next.js 16, React, TypeScript, Lucide |
| **API and service layer** | Python 3.12, Conda, FastAPI, Pydantic, SQLAlchemy |
| **Document processing** | Docling, OpenPyXL, Python worker |
| **Embedding and semantic search** | Sentence Transformers (`all-MiniLM-L6-v2`), pgvector |
| **Lexical retrieval and fusion** | PostgreSQL full-text search, reciprocal rank fusion |
| **Evidence reranking** | Cross-encoder (`ms-marco-MiniLM-L-6-v2`) |
| **LLM inference** | Groq API, `openai/gpt-oss-20b`, structured JSON output |
| **Object storage integration** | Amazon S3, Boto3, configurable storage adapter |
| **Persistence and schema** | PostgreSQL 17, Alembic |
| **Delivery and quality** | Docker, Docker Compose, GitHub Actions, pytest, evaluation scripts |

## Evaluation & results

The repository contains the test cases, scoring scripts, and original JSON/Markdown reports in [`backend/evaluation/`](backend/evaluation/) and [`docs/EVALUATION.md`](docs/EVALUATION.md). The retrieval benchmark uses **15 synthetic test queries**, including **12 answerable questions** and **three access/no-result probes**, against the original **three-document indexed corpus**. It reports document-level relevance at `K=5`.

### Retrieval benchmark

| Retrieval approach | Document Recall@5 | MRR@5 | Warm p50 latency | Warm p95 latency |
|---|---:|---:|---:|---:|
| PostgreSQL full-text | 1.000 | **0.889** | **3.6 ms** | 22.5 ms |
| pgvector semantic | 1.000 | 0.635 | 10.8 ms | 12.9 ms |
| Hybrid + RRF + reranking | 1.000 | 0.833 | 115.4 ms | 265.1 ms |

The retrieval experiment separates **coverage**, **ranking quality**, and **latency**. All three approaches reached the relevant document within five results in this small corpus. The keyword baseline achieved the highest observed MRR@5, while hybrid reranking had higher retrieval latency—a useful trade-off to quantify before optimizing a larger production collection.

### Answer, security, and regression checks

| Evaluation signal | Recorded result | Evaluation scope |
|---|---|---|
| Automated answer contract checks | **10 / 15** | Original answer-quality pilot |
| Unauthorized source exposures | **0 observed** | Tested role/tenant scenarios |
| Full answer API latency | p50 **3.867 s** · p95 **16.689 s** | Original B3 pilot |
| Backend regression suite | **37 passed, 1 skipped** | Latest recorded backend run |
| S3 adapter tests | **4 passed** | Mocked adapter/storage tests |

The automated answer checks evaluate response status, citations, access rules, and other contract requirements; they are **not a claim-level faithfulness score**. Evaluation cases, outputs, and scoring methods remain available for independent review and extension.

### Reproduce the evaluation

From `backend/` in the configured Conda environment:

```cmd
python -m pytest -q
python -m pytest -q tests\test_s3_storage_adapter.py
python scripts\evaluate_retrieval.py
python scripts\evaluate_security.py
python scripts\evaluate_answers.py
```

The retrieval and answer benchmarks require the configured database, indexed sample documents, and relevant model/provider access. For methodology and report interpretation, see [`docs/EVALUATION.md`](docs/EVALUATION.md).

## Getting started

### Prerequisites

- Python 3.12 and Conda
- Node.js 24 with npm
- Docker Desktop for PostgreSQL/pgvector and optional full-container execution
- Groq API key for knowledge-answer generation
- AWS credentials and a private S3 bucket when using Amazon S3 storage

### 1. Clone the repository and create the environment

```cmd
git clone https://github.com/Thathsarani-Sandarekha/enterprise-knowledge-intelligence.git
cd enterprise-knowledge-intelligence
conda create -n docmind_env python=3.12 -y
conda activate docmind_env
cd backend
python -m pip install -r requirements.txt
```

Create `backend/.env` using the configuration below, substituting your own credential values:

```dotenv
APP_MODE=local
DEV_API_KEY=replace_with_private_development_key
DATABASE_URL=postgresql+psycopg://eki:local_only_password@localhost:5433/eki
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
STORAGE_BACKEND=local
```

### 2. Start PostgreSQL and apply migrations

From the `backend/` directory:

```cmd
cd ..
docker compose up -d db
cd backend
python -m alembic upgrade head
```

### 3. Start the API, ingestion worker, and frontend

**Terminal A — FastAPI** (from `backend/`):

```cmd
conda activate docmind_env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal B — worker** (from the repository root):

```cmd
conda activate docmind_env
cd backend
python -m app.worker
```

**Terminal C — Next.js** (from the repository root):

```cmd
cd frontend
npm ci
```

Create `frontend/.env.local`:

```dotenv
BACKEND_API_URL=http://127.0.0.1:8000
DEV_API_KEY=replace_with_private_development_key
```

Then launch:

```cmd
npm run dev
```

Open **http://localhost:3000** for the application or **http://127.0.0.1:8000/docs** for interactive FastAPI documentation. Select *Studio Administrator* to upload hospitality example documents from [`samples/hospitality/`](samples/hospitality/).

### Amazon S3 configuration

Set `STORAGE_BACKEND=s3` together with the configured bucket and region in `backend/.env`. Boto3 resolves permissions through its supported AWS credential providers.

```dotenv
STORAGE_BACKEND=s3
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-private-bucket-name
S3_KEY_PREFIX=hospitality-documents
```

Validate the storage adapter with the committed tests and optional bucket smoke script:

```cmd
cd backend
python -m pytest -q tests\test_s3_storage_adapter.py
python -m scripts.s3_storage_smoke
```

See [`docs/S3_SETUP.md`](docs/S3_SETUP.md) for configuration details.

### Docker Compose

The base Compose file starts PostgreSQL. The demo overlay defines the application services:

```cmd
docker compose -f docker-compose.yml -f compose.demo.yml config --quiet
docker compose -f docker-compose.yml -f compose.demo.yml up --build -d
docker compose -f docker-compose.yml -f compose.demo.yml ps
```

### Developer checks

```cmd
cd backend
python -m pytest -q
cd ..\frontend
npm run typecheck
npm run build
```

## API overview

The Next.js server gateway forwards application traffic to versioned FastAPI endpoints.

| Method | Endpoint | Engineering responsibility |
|---|---|---|
| `GET` | `/health` | API health check |
| `POST` | `/api/v1/documents` | Validate, store, and enqueue an uploaded document |
| `GET` | `/api/v1/documents` | List accessible document records |
| `GET` | `/api/v1/documents/{id}` | Retrieve authorized document metadata |
| `PUT` | `/api/v1/documents/{id}/permissions` | Update document grants |
| `POST` | `/api/v1/knowledge/search` | Permission-scoped hybrid search and reranking |
| `POST` | `/api/v1/knowledge/ask` | Structured answer generation with source citations |
| `POST` | `/api/v1/search/vector` | Vector retrieval endpoint |

Example knowledge request:

```json
{
  "question": "What could delay the guestroom seating renovation at Solstice Grand Resort?",
  "project_code": "SGR-2025",
  "top_k": 5
}
```

For development requests, the API uses the configured development key and demo principal headers; the Next.js server-side gateway supplies the key for UI requests.

## Repository structure

```text
enterprise-knowledge-intelligence/
├── README.md
├── .github/workflows/              # Backend, frontend, S3 and Docker checks
├── backend/
│   ├── app/
│   │   ├── routes/                 # Document, principal, search and knowledge APIs
│   │   ├── services/               # Extraction, storage, retrieval, ranking, security, answers
│   │   └── worker.py               # Background ingestion worker
│   ├── migrations/                 # Alembic schema migrations
│   ├── evaluation/                 # Evaluation datasets, metrics and selected reports
│   ├── scripts/                    # Evaluation and smoke-test commands
│   ├── tests/                      # API, access-control, RAG and storage tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                        # Next.js pages and API gateway
│   ├── components/                 # Document library and knowledge assistant
│   └── package.json
├── docs/
│   ├── architecture/               # SVG/PNG diagrams + editable renderer
│   ├── EVALUATION.md
│   ├── PORTFOLIO_CASE_STUDY.md
│   └── DEMO_SCRIPT.md
├── samples/hospitality/            # Reproducible project documents
├── docker-compose.yml
└── compose.demo.yml
```

## Engineering challenges & next iterations

| Engineering challenge | Solution or extension |
|---|---|
| **Evidence attribution** | Preserve source locators and validate source quotations; expand claim-level semantic review with a larger test set |
| **Retrieval trade-offs** | Benchmark lexical/vector/hybrid methods and tune reranking depth against latency and document diversity |
| **Access-aware RAG** | Enforce backend document scope and map verified enterprise user claims into the same authorization model |
| **Document lifecycle reliability** | Use persistent worker states, validation and deduplication; extend operational metrics and recovery scenarios |
| **Cloud scaling** | Package independent frontend/API/worker services for ECS and use managed AWS observability/storage/persistence patterns |

## Project resources

- [Architecture and workflow visuals](docs/architecture/)
- [Evaluation methodology and results](docs/EVALUATION.md)
- [3–5 minute demo script](docs/DEMO_SCRIPT.md)
- [Technical case study](docs/PORTFOLIO_CASE_STUDY.md)
- [S3 configuration guide](docs/S3_SETUP.md)

---

<div align="center">

**ASTERIA / STUDIO**

*Design knowledge, connected to its evidence.*

</div>
