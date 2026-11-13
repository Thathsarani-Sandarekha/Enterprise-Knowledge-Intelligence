# Evaluation and Limitations — Asteria Studio

## Retrieval pilot, 12 answerable of 15 total queries, 3 synthetic documents

| Method | Doc Recall@5 | Doc MRR@5 | Warm p50 ms | Warm p95 ms |
|---|---:|---:|---:|---:|
| Keyword | 1.0000 | **0.8889** | 3.6 | 22.5 |
| Vector | 1.0000 | 0.6347 | 10.8 | 12.9 |
| Hybrid + RRF + rerank | 1.0000 | 0.8333 | 115.4 | 265.1 |

These are small-corpus pilot metrics. **Do not claim hybrid retrieval outperformed keyword on this dataset.** Source: local `backend/evaluation/results/retrieval_pilot.md`.

## Access and security

- Six simulated identities, document grants and tenant filtering verified in smoke scenarios; unauthorized source exposure observed: 0 in the pilot.
- Nine security/citation/PII helper unit tests passed in the B2 run; three adversarial pilot prompts passed. These do **not** establish production security certification.
- `x-demo-user` is spoofable with the development API key. Before public deployment, implement real SSO/OIDC plus authorization at every API and object access.
- PII helper is not evidence of end-to-end log redaction or compliance.

## Answer-quality pilot (original B3 run)

- 15 cases, 14 API responses and 1 API error; **10/15 automated rule passes (66.67%)**.
- Full API latency p50: **3,867 ms**, p95: **16,688.5 ms** (run-dependent).
- Some answerable requests were incorrectly abstained due to citation verification; later debugging showed exact-quote mismatches and retry timeouts. Do not represent this as resolved without a new passing full run.
- Faithfulness, semantic citation correctness and hallucination frequency **not yet measured manually**.
- Automatic fact-pattern matches are *not* the same as factual accuracy.

## Reproducibility

- Backend: `cd backend && python -m pytest -q` (latest local run: 33 passed, 1 skipped; repeat after patch).
- Retrieval pilot: `cd backend && python scripts/evaluate_retrieval.py` (requires seeded documents, DB and models).
- Answer pilot: `cd backend && python scripts/evaluate_answers.py` (calls Groq and consumes provider quota; timeouts possible).
- S3 unit tests: `cd backend && python -m pytest -q tests/test_s3_storage_adapter.py` (mocked, no AWS charges).
- S3 live smoke: `cd backend && python -m scripts.s3_storage_smoke` only after authenticating with a private bucket.

**Methodological limits:** all source records are synthetic, corpus size is tiny, retrieval labels are small and human selected, CI/live cloud verification is pending, and actual customer usage is not claimed.
