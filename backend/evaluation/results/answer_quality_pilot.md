# Asteria Studio — B3 Answer Quality Pilot

**Synthetic 3-document corpus; preliminary local evaluation. Not production validation.**
UTC: 2026-11-12T10:24:51.835611+00:00
Model requested: `openai/gpt-oss-20b`
Cases executed: 15; responses: 14; errors: 1

## Automatically measured signals

| Signal | Result |
|---|---:|
| Reference-fact / source / status rule pass rate | 0.6667 |
| Reference fact pattern coverage (not semantic correctness) | 0.4783 |
| Full-abstention precision | 0.4286 |
| Full-abstention recall | 1.0000 |
| Forbidden citation-source exposures | 0 |
| Forbidden answer-pattern exposures | 0 |
| Full API latency p50 (ms) | 3867.0000 |
| Full API latency p95 (ms) | 16688.5000 |
| Input tokens reported by API (partial possible) | 9627 |
| Output tokens reported by API (partial possible) | 1341 |
| Responses lacking token counts | 8 |
| Exact provider cost (USD) | not measured |

## Per-case evidence

| ID | Role | Kind | API status | Automatic checks | Facts | Cites | Latency (ms) |
|---|---|---|---|---|---|---:|---:|
| A01 | aster-procurement | answerable | answered | PASS | 2/2 | 1 | 863.2000 |
| A02 | aster-procurement | answerable | answered | PASS | 2/2 | 1 | 880.8000 |
| A03 | aster-procurement | answerable | insufficient_evidence | CHECK | 0/6 | 0 | 1223.8000 |
| A04 | aster-procurement | answerable | insufficient_evidence | CHECK | 0/3 | 0 | 1171.6000 |
| A05 | aster-admin | answerable | answered | PASS | 1/1 | 2 | 6510.2000 |
| A06 | aster-admin | answerable | insufficient_evidence | CHECK | 0/1 | 0 | 16318.0000 |
| A07 | aster-designer | answerable | HTTPStatusError | CHECK | 0/3 | 0 | 9503.8000 |
| A08 | aster-pm | answerable | answered | PASS | 1/1 | 1 | 657.4000 |
| A09 | aster-designer | answerable | answered | PASS | 5/5 | 3 | 15345.0000 |
| A10 | aster-pm | answerable | insufficient_evidence | CHECK | 0/2 | 0 | 13392.7000 |
| A11 | aster-designer | unavailable_detail | answered | PASS | - | 1 | 9943.2000 |
| A12 | aster-procurement | unavailable_detail | insufficient_evidence | PASS | - | 0 | 17376.7000 |
| A13 | rival-designer | unanswerable | insufficient_evidence | PASS | - | 0 | 18.9000 |
| A14 | rival-admin | unanswerable | insufficient_evidence | PASS | - | 0 | 18.0000 |
| A15 | aster-admin | unanswerable | insufficient_evidence | PASS | - | 0 | 12165.7000 |

## What is NOT measured automatically

- **Answer correctness:** regex fact matches do not detect contradictory statements or unsupported extra claims.
- **Faithfulness / hallucination rate:** requires claim-by-claim inspection against source evidence.
- **Semantic citation accuracy:** `citation_integrity=passed` confirms real quotations, not whether cited text supports each answer claim.
- **Price protection:** simple patterns and source filenames are screening checks, not a substitute for policy/security assessment.
- **Cost:** Groq pricing is not assumed; some abstention responses omit token usage. Reported tokens may therefore be incomplete.
- **Latency:** response time includes the server, retrieval, and Groq. Cold/warm model state and network conditions are not controlled across machines.

## Required manual review

Review original synthetic documents and all returned claims using `answer_quality_review_template.json`.
Populate each case with atomic claims and whether evidence supports each claim and its citation.
Run `python scripts/score_answer_reviews.py` after review to quantify faithfulness, semantic citation correctness,
hallucinations and manual answer correctness. Keep those metrics labeled **not evaluated** until the review is done.

## Baseline context

B1 retrieval pilot: keyword MRR@5 0.8889; vector 0.6347; hybrid 0.8333, all on the same small 3-document corpus.
B3 evaluates full answers, not retrieval ranking, so do not compare their latencies directly.
