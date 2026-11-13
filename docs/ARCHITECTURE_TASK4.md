# Task 4 Architecture — Asteria Hospitality Studio (fictional)

```mermaid
flowchart TD
    UI[Swagger / future Next.js UI] --> API[FastAPI]
    API --> DEV[Local demo key + simulated principal]
    DEV --> ACL[Tenant + document-role SQL predicates]
    ACL --> K[Postgres full-text GIN search]
    ACL --> V[pgvector cosine semantic search]
    K --> R[Reciprocal Rank Fusion]
    V --> R
    R --> CE[Local cross-encoder reranker]
    CE --> G[Groq GPT-OSS 20B strict JSON]
    G --> C[Deterministic citation integrity checks]
    C --> O[Answer + DB-provided source locations / abstention]
    INGEST[Existing Task 3 Docling / XLSX ingestion worker] --> DB[(PostgreSQL documents + chunks + grants)]
    DB --> K
    DB --> V
```

**Trust boundary:** The `DEV` node is local-only simulation, not identity verification. Retrieval authorization must precede all model calls. SQL filtering is repeated on both retrieval branches; no candidate may bypass it.

**Future architecture:** Verified OIDC/JWT authentication + tenant membership claims, policy-based authorization and RLS defense in depth, malicious-document quarantine, PII-aware telemetry, observability, and signed source-document URLs.

**Project provenance:** Example luxury-hotel renovation data is synthetic, and the architecture is not associated with any real reference company.
