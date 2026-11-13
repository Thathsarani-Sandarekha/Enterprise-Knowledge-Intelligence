# Asteria Studio — Security Smoke Evaluation

**Local demo identities are spoofable; this is not a production authentication or penetration test.**
Run (UTC): 2026-11-12T09:44:43.990585+00:00
Base URL: http://127.0.0.1:8000

| Identity | Document count | Search evidence count | Forbidden source exposed | Result |
|---|---:|---:|---|---|
| aster-admin | 3 | 6 | no | PASS |
| aster-procurement | 3 | 6 | no | PASS |
| aster-designer | 2 | 6 | no | PASS |
| aster-pm | 2 | 6 | no | PASS |
| rival-designer | 0 | 0 | no | PASS |
| rival-admin | 0 | 0 | no | PASS |

## Optional model-answer checks

- aster-procurement: answered — PASS; 1558.9 ms
- aster-designer: answered — PASS; 1091.1 ms
- rival-designer: insufficient_evidence — PASS; 19.3 ms

## Limitations
- Only three synthetic documents and six local demo identities were tested.
- The negative checks exercise SQL-scoped retrieval and response behavior, not identity verification.
- This does not test malicious content embedded in stored documents, production key handling, or parser sandboxing.
- PII redaction in application logs and model responses is NOT established by this script.
- Source existence and verbatim quote verification do not prove claim-level faithfulness.
- Do not report zero prompt-injection success or zero PII leakage without dedicated evaluations.

Overall: **PASS**
