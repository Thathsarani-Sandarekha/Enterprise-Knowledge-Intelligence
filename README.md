<div align="center">

# Asteria Studio
### Enterprise Knowledge Intelligence Platform

**Evidence-grounded RAG for hospitality architecture, interior design, and project operations.**

A unified workspace for processing project documents, discovering relevant information, and generating answers with verifiable source citations and document-level access control.

[Architecture](#system-architecture) · [Key Features](#key-capabilities) · [Demo](#application-demo) · [Engineering](#engineering-decisions) · [Evaluation](#evaluation) · [Getting Started](#getting-started)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=flat-square&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-TypeScript-111827?style=flat-square&logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Structured%20LLM%20Generation-F55036?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![Amazon S3](https://img.shields.io/badge/AWS-S3%20%7C%20Boto3-FF9900?style=flat-square&logo=amazons3&logoColor=white)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)

</div>

---

## Overview

Hospitality design teams coordinate decisions across architectural briefs, material approvals, supplier quotations, fire-document registers, and renovation schedules. Important details live in different PDF, Word, and Excel files. An interior designer may need an approved material specification; procurement may need pricing and lead times; a project manager may need to identify outstanding approval conditions.

**Asteria Studio** turns these scattered records into a searchable knowledge workspace. Users ask questions in natural language, receive answers supported by source passages, and see only the documents authorized for their role and tenant.

The project brings together **multi-format document ingestion, asynchronous processing, PostgreSQL/pgvector, hybrid retrieval, cross-encoder reranking, Groq-based answer generation, and backend citation verification** within a modular Next.js and FastAPI application.

**Business scenario:** A hospitality interior-design consultancy working on luxury hotel renovation projects. The public walkthrough uses synthetic project documentation for **Solstice Grand Resort**.

## System architecture

![Asteria Studio — High-level enterprise knowledge intelligence architecture](docs/architecture/asteria-system-overview.png)

*One high-level view of the application services, document ingestion and RAG pipelines, storage responsibilities, and AWS deployment design.*

The platform has **three application services**: a **Next.js web workspace**, a **FastAPI backend**, and a **Python ingestion worker**. They share PostgreSQL for document metadata, indexing, authorization, and processing jobs. The storage adapter also supports **Amazon S3** for original document files.

### 1. Document ingestion and indexing

```text
Administrator uploads PDF / DOCX / XLSX
    ↓
Next.js → FastAPI (validation, storage, document registration)
    ├──→ Amazon S3 / configured storage (original file)
    └──→ PostgreSQL (queued ingestion job)
                  ↓
           Python Worker picks up job
                  ↓
           Docling / OpenPyXL extraction
                  ↓
           Source-aware text chunking
                  ↓
           Sentence Transformers embeddings
                  ↓
           PostgreSQL + pgvector indexing
                  ↓
           Processing status → Ready
```

The worker processes uploads independently of interactive API requests. Source metadata is retained with chunks so search results can be traced back to a document and its supporting excerpt.

### 2. Real-time question answering

```text
User question → Next.js → FastAPI
                              ↓
                  Tenant + document access checks
                              ↓
                Authorized hybrid retrieval
                 ├── PostgreSQL keyword search
                 └── pgvector semantic search
                              ↓
                    Reciprocal Rank Fusion
                              ↓
                     Cross-encoder reranking
                              ↓
                 Groq structured answer generation
                              ↓
                 Backend citation verification
                              ↓
                   FastAPI → Next.js
                     Answer + source excerpts
```

The retrieval step uses both **exact terminology** (such as material and project codes) and **semantic similarity** (questions phrased differently from the source). The final response contains inspectable evidence excerpts, checked against the retrieved passages.

### 3. Containerization and AWS architecture

| Component | Responsibility |
|---|---|
| **Docker / Docker Compose** | Package the web, API, and worker services; coordinate the development environment and database |
| **GitHub Actions** | Automated Python/Next.js checks and container-image build workflows |
| **Amazon ECR** | Registry for application container images in the AWS deployment design |
| **Amazon ECS Fargate** | Run the Next.js, FastAPI, and worker containers without managing EC2 servers |
| **Application Load Balancer** | Route incoming HTTPS application traffic to the web service |
| **Amazon RDS (PostgreSQL + pgvector)** | Managed relational and vector database for indexed knowledge, grants, and ingestion jobs |
| **Amazon S3** | Original PDF, DOCX, and XLSX storage, accessed through the Boto3 adapter |
| **AWS IAM / CloudWatch** | AWS service permissions, centralized logs, metrics, and monitoring |

This deployment design uses the **same application services and processing logic** as the Docker-based implementation. The application code and AWS infrastructure responsibilities are kept separate.

## Key capabilities

| Capability | How it works |
|---|---|
| **Document library** | Upload, validate, deduplicate, organize, and track processing of PDF, DOCX, and XLSX documents |
| **Background processing** | PostgreSQL-backed ingestion jobs and a separate Python worker |
| **Document intelligence** | Docling for PDF/DOCX, OpenPyXL for spreadsheets, and source-aware chunking |
| **Hybrid knowledge search** | PostgreSQL full-text retrieval + 384-dimensional Sentence Transformers embeddings in pgvector |
| **Relevance ranking** | Reciprocal Rank Fusion (RRF) followed by cross-encoder reranking |
| **Grounded Q&A** | Groq-generated structured answers with citations verified against retrieved source excerpts |
| **Permission-aware retrieval** | Tenant and document-grant restrictions applied in the backend search path |
| **Document storage** | Boto3-based Amazon S3 adapter, with a configurable filesystem storage option |
| **Engineering quality** | Database migrations, pytest, evaluation scripts, Dockerfiles, Compose, and GitHub Actions |

## Application demo

The demonstration uses a synthetic luxury-hotel renovation scenario to illustrate **project intelligence, evidence verification, and role-based access**.

| Role | Demonstration |
|---|---|
| **Studio Administrator** | Manages the document library, uploads project records, and assigns access grants |
| **Interior Designer** | Searches permitted design approvals and material specifications |
| **Procurement Specialist** | Searches supplier quotations, prices, and delivery information where granted |
| **Project Manager** | Reviews accessible project briefs, approvals, and outstanding conditions |
| **Another studio's user** | Remains isolated from Asteria Studio's project documents |

The **View As** selector lets the public demo show multiple predefined identities quickly. In an organization-wide application, user identities would come from the sign-in system while the backend retains responsibility for enforcing access rules.

### Example workflow — Solstice Grand Resort

**1. Find approval conditions**

> What could delay the guestroom seating renovation at Solstice Grand Resort, and what must the team check before ordering the upholstery?

The assistant locates the relevant approval conditions and points back to the supporting project records.

**2. Verify purchasing information**

> What is the supplier's quoted price and delivery lead time for the approved upholstery at Solstice Grand Resort?

The synthetic supplier quotation lists **UPH-FR-220**, supplied by **Northstar Contract Textiles**, at **USD 145 per yard** and **21 days**. Procurement can inspect the supporting quotation excerpt; design-only access does not expose that restricted commercial source.

**3. Audit the evidence**

Open a cited result to inspect its document name, source location, and verified quotation.

### Video walkthroughs

Explore Asteria Studio through three demonstration videos covering the working application, technical architecture, and key AI engineering capabilities.

### 1. Full Application Demo
See document ingestion, RAG-powered question answering, verified citations, and role-based document access.

🎥 [Watch Application Demo](YOUTUBE_LINK)

### 2. Technical Architecture Walkthrough
Explore FastAPI, Docling, PostgreSQL/pgvector, hybrid retrieval, RRF, cross-encoder reranking, Groq, and the AWS deployment architecture.

🎥 [Watch Architecture Walkthrough](YOUTUBE_LINK)

### 3. Project Overview — 60-Second Demo
A quick introduction to the business problem, AI solution, and key capabilities.

🎥 [Watch 60-Second Demo](YOUTUBE_SHORTS_LINK)

## Engineering decisions

**Why use an ingestion worker?** Document parsing and embedding generation can take longer than a normal API request. Queued jobs keep file processing separate from interactive search and allow retries and status tracking.

**Why PostgreSQL with pgvector?** The same database can store structured document records, access grants, full-text indexes, and vector embeddings. This simplifies the relationship between search evidence and its authorized source document.

**Why hybrid retrieval?** Architectural records mix precise identifiers (for example `UPH-FR-220` or `FR-DOC-220`) with descriptive project notes. Keyword retrieval helps with exact matches; embeddings help with semantic matches. RRF merges the two ranked lists and a cross-encoder reranks the candidates.

**Why Amazon S3?** Original document files have different storage needs from indexed text and vectors. The Boto3 storage adapter separates original-file storage from the searchable knowledge index and allows the application to use a private S3 bucket.

**Why backend citation verification?** Generated answers can contain inaccurate references. The backend checks cited evidence identifiers and quotation text against the retrieved chunks before presenting source-backed responses.

**Why enforce permissions before retrieval?** Access checks must constrain the candidate document set before evidence is supplied to the LLM. Restricting only the UI would not protect information returned from backend searches.

## Technology stack

| Layer | Technologies |
|---|---|
| Web application | Next.js 16, React, TypeScript |
| API and application logic | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| Parsing and ingestion | Python worker, Docling, OpenPyXL |
| Embeddings and reranking | Sentence Transformers, local cross-encoder |
| Retrieval and persistence | PostgreSQL, pgvector, PostgreSQL full-text search, Alembic |
| Language model | Groq API (`openai/gpt-oss-20b`) |
| Object storage | Amazon S3 adapter using Boto3 |
| Build and quality | Conda, Docker, Docker Compose, GitHub Actions, pytest |
| AWS deployment design | Application Load Balancer, ECR, ECS Fargate, RDS, S3, IAM, CloudWatch |

## Evaluation

The repository includes repeatable retrieval, answer-quality, and security evaluations against a curated hospitality document set.

| Evaluation | Observed result | Scope |
|---|---:|---|
| Document Recall@5 — keyword / vector / hybrid | **1.000 / 1.000 / 1.000** | 3-document synthetic pilot; 12 answerable queries |
| MRR@5 — keyword / vector / hybrid + reranking | **0.889 / 0.635 / 0.833** | Same pilot; keyword ranked highest in this sample |
| Hybrid retrieval latency (warm p50) | **115.4 ms** | Measured retrieval run |
| Automated answer-quality rule checks | **10/15 passed (66.67%)** | API/citation/access contracts, not a manual correctness rating |
| Forbidden-source exposure | **0 observed** | Tested role/tenant scenarios in the pilot |

The dataset and scripts are intentionally reproducible, making it possible to compare retrieval methods, diagnose citation failures, and extend the evaluation corpus over time.

**Reproduce the checks** from the `backend/` directory:

```cmd
python -m pytest -q
python scripts\evaluate_retrieval.py
python scripts\evaluate_security.py
python scripts\evaluate_answers.py
```

See [`docs/EVALUATION.md`](docs/EVALUATION.md), [`backend/evaluation/`](backend/evaluation/), and the saved pilot reports under `backend/evaluation/results/` for methodology and results.

## Getting started

### Prerequisites

- Python **3.12** and Conda
- Node.js **24** and npm
- Docker Desktop (for PostgreSQL/pgvector)
- A Groq API key
- AWS credentials and a private bucket if using the Amazon S3 storage adapter

### 1. Create the Python environment

From the repository root (Windows CMD / Anaconda Prompt):

```cmd
git clone https://github.com/Thathsarani-Sandarekha/enterprise-knowledge-intelligence.git
cd enterprise-knowledge-intelligence
conda create -n docmind_env python=3.12 -y
conda activate docmind_env
cd backend
python -m pip install -r requirements.txt
```

Create `backend/.env`:

```dotenv
APP_MODE=local
DEV_API_KEY=replace_with_a_private_development_key
DATABASE_URL=postgresql+psycopg://eki:local_only_password@localhost:5433/eki
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
STORAGE_BACKEND=local
```

Keep credentials in environment variables or ignored `.env` files, not in Git.

### 2. Start PostgreSQL and run migrations

From the project root:

```cmd
cd ..
docker compose up -d db
cd backend
python -m alembic upgrade head
```

### 3. Start the three application processes

**Terminal A — FastAPI** (from `backend/`):

```cmd
conda activate docmind_env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal B — Python worker** (from the repository root):

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

Create `frontend/.env.local` with the same development key used by the backend:

```dotenv
BACKEND_API_URL=http://127.0.0.1:8000
DEV_API_KEY=replace_with_a_private_development_key
```

Start the frontend:

```cmd
npm run dev
```

Open **http://localhost:3000**. FastAPI's interactive API documentation is available at **http://127.0.0.1:8000/docs**.

Select **Studio Administrator** in the demonstration role switcher, upload the examples from `samples/hospitality/`, and confirm processing reaches **Ready** before running the example searches.

### Amazon S3 document storage

The Boto3 adapter uses the normal AWS credential chain. Configure `backend/.env` to select S3 for new uploads:

```dotenv
STORAGE_BACKEND=s3
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-private-bucket
S3_KEY_PREFIX=asteria-documents
```

```cmd
cd backend
python -m pytest -q tests\test_s3_storage_adapter.py
```

See [`docs/S3_SETUP.md`](docs/S3_SETUP.md) for bucket permissions and optional integration testing.

### Docker Compose application profile

In addition to the database Compose file, the application overlay defines the Dockerized services:

```cmd
docker compose -f docker-compose.yml -f compose.demo.yml config --quiet
docker compose -f docker-compose.yml -f compose.demo.yml up --build -d
docker compose -f docker-compose.yml -f compose.demo.yml ps
```

## API overview

The Next.js server gateway forwards requests to versioned FastAPI endpoints.

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health` | API health |
| `GET` / `POST` | `/api/v1/documents` | List authorized documents / upload a document |
| `GET` | `/api/v1/documents/{id}` | Read document metadata |
| `POST` | `/api/v1/knowledge/search` | Permission-scoped hybrid retrieval |
| `POST` | `/api/v1/knowledge/ask` | Structured answer with source citations |
| `POST` | `/api/v1/search/vector` | Vector retrieval diagnostic |

Example request for `/api/v1/knowledge/ask`:

```json
{
  "question": "What could delay the guestroom seating renovation at Solstice Grand Resort?",
  "project_code": "SGR-2025",
  "top_k": 5
}
```

The project includes a controlled development API key and demo identities for testing the access-control flows. The web application passes requests through its server-side gateway rather than exposing the backend development key in browser code.

## Project structure

```text
enterprise-knowledge-intelligence/
├── backend/
│   ├── app/
│   │   ├── routes/               # Documents, knowledge, search, permissions
│   │   ├── services/             # Extraction, retrieval, ranking, answers, storage
│   │   └── worker.py             # Background ingestion
│   ├── migrations/               # Alembic schemas and ACL tables
│   ├── evaluation/               # Cases, metrics and saved pilot results
│   ├── scripts/                  # Evaluation and smoke-test commands
│   ├── tests/                    # Unit and security tests
│   ├── requirements.txt          # Backend dependency manifest
│   └── Dockerfile
├── frontend/
│   ├── app/                      # Next.js routes and API gateway
│   ├── components/               # Document library and knowledge search
│   ├── Dockerfile
│   └── package.json
├── samples/hospitality/          # Synthetic project PDFs, DOCX, XLSX
├── docs/
│   ├── architecture/             # System overview image
│   ├── ARCHITECTURE.md
│   ├── EVALUATION.md
│   ├── PORTFOLIO_CASE_STUDY.md
│   ├── DEMO_SCRIPT.md
│   └── S3_SETUP.md
├── .github/workflows/           # CI and container build checks
├── docker-compose.yml
├── compose.demo.yml
└── README.md
```

<div align="center">

**Asteria Studio** · Document intelligence · Permission-aware hybrid RAG · Source-verifiable answers

</div>
