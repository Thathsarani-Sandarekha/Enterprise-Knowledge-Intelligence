# Asteria Studio — Retrieval Pilot Evaluation

**Synthetic, three-document demo corpus; NOT a production-scale accuracy benchmark.**
Run (UTC): 2026-11-12T09:06:32.851515+00:00
Queries: 15 | Top K: 5 | Corpus: 3 ready documents (across all tenants)

| Retrieval | Doc Recall@K | Doc MRR@K | p50 (ms) | p95 (ms) | Forbidden exposures | Empty-result violations |
|---|---:|---:|---:|---:|---:|---:|
| keyword | 1.0000 | 0.8889 | 3.6000 | 22.5000 | 0 | 0 |
| vector | 1.0000 | 0.6347 | 10.8000 | 12.9000 | 0 | 0 |
| hybrid_rrf_rerank | 1.0000 | 0.8333 | 115.4000 | 265.1000 | 0 | 0 |

## Interpretation and limitations
- Document-level relevance was manually labeled; multiple chunks from the same document count once for Recall@K.
- MRR@K is based on the rank of the first relevant *chunk* mapped to its source document.
- Queries with no labeled accessible document are excluded from Recall and MRR averages; access checks are reported separately.
- Warm-model local timing measures retrieval calls, not end-to-end Groq answer time. This run does not test answer faithfulness.
- The corpus contains only three synthetic documents. No generalization or superiority claim should be made from this pilot.
- These local demo identities are spoofable by anyone with the dev API key; this is not production authentication.

## Case-by-case results

| Case | Role | Method | Recall | RR | Latency (ms) | Forbidden exposure |
|---|---|---|---:|---:|---:|---|
| Q01 | aster-procurement | keyword | 1.00 | 1.00 | 9.6 | none |
| Q01 | aster-procurement | vector | 1.00 | 0.25 | 12.2 | none |
| Q01 | aster-procurement | hybrid_rrf_rerank | 1.00 | 1.00 | 265.1 | none |
| Q02 | aster-procurement | keyword | 1.00 | 1.00 | 3.6 | none |
| Q02 | aster-procurement | vector | 1.00 | 0.20 | 10.5 | none |
| Q02 | aster-procurement | hybrid_rrf_rerank | 1.00 | 0.50 | 228.8 | none |
| Q03 | aster-procurement | keyword | 1.00 | 1.00 | 3.6 | none |
| Q03 | aster-procurement | vector | 1.00 | 0.33 | 10.8 | none |
| Q03 | aster-procurement | hybrid_rrf_rerank | 1.00 | 1.00 | 236.1 | none |
| Q04 | aster-procurement | keyword | 1.00 | 1.00 | 3.4 | none |
| Q04 | aster-procurement | vector | 1.00 | 0.50 | 10.7 | none |
| Q04 | aster-procurement | hybrid_rrf_rerank | 1.00 | 1.00 | 233.7 | none |
| Q05 | aster-admin | keyword | 1.00 | 0.33 | 4.2 | none |
| Q05 | aster-admin | vector | 1.00 | 0.50 | 10.5 | none |
| Q05 | aster-admin | hybrid_rrf_rerank | 1.00 | 0.50 | 197.8 | none |
| Q06 | aster-admin | keyword | 1.00 | 0.33 | 3.3 | none |
| Q06 | aster-admin | vector | 1.00 | 1.00 | 11.2 | none |
| Q06 | aster-admin | hybrid_rrf_rerank | 1.00 | 1.00 | 239.8 | none |
| Q07 | aster-designer | keyword | 1.00 | 1.00 | 3.2 | none |
| Q07 | aster-designer | vector | 1.00 | 1.00 | 11.6 | none |
| Q07 | aster-designer | hybrid_rrf_rerank | 1.00 | 1.00 | 86.6 | none |
| Q08 | aster-designer | keyword | 1.00 | 1.00 | 22.5 | none |
| Q08 | aster-designer | vector | 1.00 | 1.00 | 12.6 | none |
| Q08 | aster-designer | hybrid_rrf_rerank | 1.00 | 1.00 | 87.3 | none |
| Q09 | aster-designer | keyword | 1.00 | 1.00 | 3.6 | none |
| Q09 | aster-designer | vector | 1.00 | 1.00 | 9.3 | none |
| Q09 | aster-designer | hybrid_rrf_rerank | 1.00 | 1.00 | 99.3 | none |
| Q10 | aster-pm | keyword | 1.00 | 1.00 | 3.9 | none |
| Q10 | aster-pm | vector | 1.00 | 0.50 | 12.9 | none |
| Q10 | aster-pm | hybrid_rrf_rerank | 1.00 | 0.50 | 115.4 | none |
| Q11 | aster-pm | keyword | 1.00 | 1.00 | 3.0 | none |
| Q11 | aster-pm | vector | 1.00 | 1.00 | 11.0 | none |
| Q11 | aster-pm | hybrid_rrf_rerank | 1.00 | 1.00 | 82.4 | none |
| Q12 | aster-procurement | keyword | 1.00 | 1.00 | 3.5 | none |
| Q12 | aster-procurement | vector | 1.00 | 0.33 | 9.7 | none |
| Q12 | aster-procurement | hybrid_rrf_rerank | 1.00 | 0.50 | 227.0 | none |
| Q13 | aster-designer | keyword | N/A | N/A | 3.6 | none |
| Q13 | aster-designer | vector | N/A | N/A | 10.7 | none |
| Q13 | aster-designer | hybrid_rrf_rerank | N/A | N/A | 91.6 | none |
| Q14 | rival-designer | keyword | N/A | N/A | 2.4 | none |
| Q14 | rival-designer | vector | N/A | N/A | 10.1 | none |
| Q14 | rival-designer | hybrid_rrf_rerank | N/A | N/A | 11.6 | none |
| Q15 | rival-admin | keyword | N/A | N/A | 1.7 | none |
| Q15 | rival-admin | vector | N/A | N/A | 11.2 | none |
| Q15 | rival-admin | hybrid_rrf_rerank | N/A | N/A | 12.4 | none |
