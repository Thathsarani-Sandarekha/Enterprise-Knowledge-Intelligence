# Case Study: Evidence-Grounded Knowledge Intelligence for Luxury Hospitality Design

## Business scenario

A fictional US hospitality architecture/interior-design consultancy manages renovation documentation across PDF fire registers, DOCX finish approvals, and XLSX supplier quotations. Designers, project managers and procurement specialists need different subsets of the information. Manual document review is slow and risks incorrect sourcing or unapproved purchases. This is an illustrative use case, not a commissioned deployment or verified client case.

## Engineering challenge

Building a search box over an LLM API is insufficient: reliable usage requires document extraction from heterogeneous formats, tenant-aware authorization, citation provenance, duplicate detection, recoverable processing, retrieval ranking, and explicit abstention when evidence is missing.

## System implemented

- FastAPI knowledge and document API, Next.js workflow UI, PostgreSQL/pgvector metadata and indexes, local embeddings, hybrid keyword/vector retrieval, RRF and reranking.
- Role/tenant-aware document grants enforced in API/database access path; simulated identities for demo only.
- Original-document local storage plus optional S3 storage adapter; S3 account integration must be verified separately from code/unit tests.
- Background worker ingests DOCX/PDF/XLSX, records chunk-level source metadata, and indexes embeddings.
- Groq structured answer generation and source-excerpt verification. Automated source validation does not imply semantic faithfulness.

## Evidence and results

- Latest reported local unit suite (before this release kit): 33 passed, 1 skipped.
- Retrieval: document-level Recall@5 1.0 in 3-document synthetic pilot; keyword MRR@5 0.889, hybrid MRR@5 0.833; warm hybrid retrieval p50 ~115ms.
- Six identity/tenant demo scenarios without observed forbidden-source exposure in smoke tests.
- Answer pilot 10/15 automatic checks passed; quote-mismatch and API timeout issues remain. Faithfulness/hallucination not yet measured.

## Decisions and tradeoffs

- **Local embeddings** lower ongoing inference dependency but introduce cold-start cost.
- **pgvector + SQL FTS** centralize document and vector search in PostgreSQL; larger-scale throughput unbenchmarked.
- **S3 remains optional** to keep an offline/low-cost demo while showing durable object-storage abstraction. Unlike cloud database or compute, it can be tested independently.
- **Permission-first retrieval** ensures model inputs are already limited to accessible chunks.
- **Abstention rather than unsupported claims** prioritizes safety at the cost of false negative answers; reliability improvement remains future work.

## What's next (not claimed complete)

Real user authentication, expanded multi-tenant evaluation, audited semantic citation fidelity, comprehensive PII lifecycle defenses, S3 live smoke in a private account, and optional ECS/RDS deployment.

**Portfolio positioning:** An implemented local-first engineering case study demonstrating RAG, data pipelines, access-aware retrieval, evaluation design and practical tradeoffs—not a production SaaS rollout.
