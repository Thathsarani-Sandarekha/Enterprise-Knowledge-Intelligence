# Asteria Studio — Technical Architecture

**Business context:** Fictional US luxury-hospitality interior design and architecture consultancy. All sample projects and suppliers are synthetic. No connection to a real client is implied.

## Current code architecture: local-first, optional S3 storage

```mermaid
flowchart TB
    U[Designer / Procurement / Project Manager] --> UI[Next.js Enterprise UI]
    UI --> GW[Next.js API gateway]
    GW --> API[FastAPI knowledge API]
    API --> AUTH[Demo identity + tenant/role authorization]
    AUTH --> UP[Document upload + validation]
    UP --> ST{Storage adapter}
    ST --> LOCAL[(Local files - default)]
    ST --> S3[(Private Amazon S3 - optional)]
    UP --> DB[(PostgreSQL metadata / grants)]
    WORKER[Durable Python ingestion worker] --> DB
    WORKER --> ST
    WORKER --> PARSE[Docling PDF/DOCX + XLSX parser]
    PARSE --> CHUNK[Text chunks and source metadata]
    CHUNK --> EMB[Local sentence-transformer embeddings]
    EMB --> PG[(PostgreSQL + pgvector / text indexes)]
    API --> SEARCH[Permission-filtered hybrid search]
    SEARCH --> PG
    SEARCH --> RRF[Reciprocal Rank Fusion]
    RRF --> RERANK[Cross-encoder reranker]
    RERANK --> LLM[Groq LLM]
    LLM --> VERIFY[Source-excerpt citation verifier]
    VERIFY --> API
```

- **Local path:** existing local files, worker, and DB remain unchanged in behavior.
- **S3 path:** implemented by optional storage adapter + upload/worker integration in this release kit. The worker downloads S3 documents to a temporary file for the existing parser. This is **not** an AWS deployment.
- **Authorization:** the demo uses a development API key and simulated identities; not production authentication. Document grants, tenant filters, and access checks are enforced at API/database retrieval level, not via public S3 links. Bucket is private and access is server-side only.
- **Citation integrity:** source-excerpt matching is a syntactic/provenance check, not proof of semantic faithfulness. Answer-quality failures and timeouts remain in the pilot.
- **PII:** limited redaction-helper tests exist; comprehensive PII removal has not been validated in application logs or data lifecycle.

## Ingestion data flow

```mermaid
flowchart LR
  A[Upload DOCX/PDF/XLSX] --> B[Validate file, hash and permissions]
  B --> C[Local or S3 object storage]
  C --> D[Queued document record]
  D --> E[Worker retrieves source]
  E --> F[Docling / spreadsheet extraction]
  F --> G[Chunk + source metadata]
  G --> H[Local embeddings]
  H --> I[pgvector + SQL full text]
  I --> J[Role/tenant-filtered retrieval]
  J --> K[RRF + reranking]
  K --> L[Groq answer]
  L --> M[Verify quotations and attach citations]
```

## Optional AWS reference deployment — NOT implemented or deployed

**This section is a design reference, not an account of deployed infrastructure.** The only AWS integration packaged by this release kit is optional S3 original-document storage via Boto3; even that needs a live account smoke test before being described as verified.

```mermaid
flowchart TB
  B[Designer or architect browser] --> CF[CloudFront and HTTPS - reference]
  CF --> ALBWEB[Public ALB for Next.js - reference]
  ALBWEB --> WEB[Next.js on ECS Fargate - reference]
  WEB --> APIGW[Amazon API Gateway HTTP API - reference]
  APIGW --> VPC[VPC Link - reference]
  VPC --> ALBAPI[Internal ALB - reference]
  ALBAPI --> API[FastAPI on ECS Fargate - reference]
  API --> RDS[(Amazon RDS PostgreSQL / pgvector - reference)]
  API --> S3[(Private Amazon S3 - optional SDK integration)]
  API --> GROQ[External Groq model API]
  WORKER[Ingestion worker on ECS Fargate - reference] --> S3
  WORKER --> RDS
  ECR[Amazon ECR images - reference] -. container images .-> WEB
  ECR -. container images .-> API
  ECR -. container images .-> WORKER
  IAM[IAM roles and Secrets Manager - reference] -. access .-> API
  IAM -. access .-> WORKER
  API -. logs / metrics .-> CW[Amazon CloudWatch - reference]
  WORKER -. logs / metrics .-> CW
  WEB -. logs / metrics .-> CW
```

- API Gateway private ECS integration needs VPC Link and a supported private target such as an Application Load Balancer; it is **not** wired directly to a private FastAPI container.
- In ECS, an **application task role** would grant scoped S3 permissions; the **task execution role** would pull ECR images and send logs to CloudWatch.
- Private S3, RDS network restrictions, TLS, proper authentication, secret handling, logging hygiene, and cost controls require a separate deployment and security review.
- This project does **not** provision ECS, ECR, RDS, API Gateway, VPC Link, ALBs, CloudFront, Secrets Manager, IAM roles or CloudWatch. Those are architecture references only.

AWS technical references:
- https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-private.html
- https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-iam-roles.html
