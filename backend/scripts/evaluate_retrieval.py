"""Read-only document-level retrieval benchmark for the Asteria Studio local demo.

Run from backend/: python scripts/evaluate_retrieval.py
No LLM calls, no database writes, and no changes to document grants.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys
from time import perf_counter
from sqlalchemy import desc, func, select

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.database import SessionLocal
from app.models import Document, DocumentChunk
from app.routes.principals import DEMO_USERS
from app.services.access import authorized_document_filter
from app.services.embeddings import embed_texts
from app.services.retrieval import keyword_expression, retrieve
from app.services.reranking import score_passages
from evaluation.metrics import recall_at_k, reciprocal_rank_at_k, summarize

DEFAULT_CASES = BACKEND / 'evaluation' / 'hospitality_questions.json'
DEFAULT_OUTPUT = BACKEND / 'evaluation' / 'results' / 'retrieval_pilot.json'


def common_predicates(principal, project_code=None):
    clauses = [
        DocumentChunk.tenant_id == principal.tenant_id,
        Document.status == 'ready',
        authorized_document_filter(principal),
    ]
    if project_code:
        clauses.append(Document.project_code == project_code)
    return clauses


def keyword_only(db, principal, question, k, project_code=None):
    lexical = keyword_expression(question)
    if not lexical:
        return []
    tsv = func.to_tsvector('english', DocumentChunk.text)
    query = func.to_tsquery('english', lexical)
    rank = func.ts_rank_cd(tsv, query)
    rows = db.execute(
        select(Document.original_filename)
        .select_from(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(*common_predicates(principal, project_code), tsv.op('@@')(query))
        .order_by(desc(rank), DocumentChunk.id)
        .limit(k)
    ).scalars().all()
    return list(rows)


def vector_only(db, principal, question, k, project_code=None):
    vector = embed_texts([question])[0]
    distance = DocumentChunk.embedding.cosine_distance(vector)
    rows = db.execute(
        select(Document.original_filename)
        .select_from(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(*common_predicates(principal, project_code))
        .order_by(distance.asc(), DocumentChunk.id)
        .limit(k)
    ).scalars().all()
    return list(rows)


def hybrid(db, principal, question, k, project_code=None):
    evidence, _ = retrieve(db, principal, question, top_k=k,
                           candidate_k=20, project_code=project_code)
    return [item.filename for item in evidence]


def run_case(db, case, k, method, fn):
    principal = DEMO_USERS[case['role']]
    started = perf_counter()
    ranked = fn(db, principal, case['question'], k, case.get('project_code'))
    latency_ms = round(1000 * (perf_counter() - started), 1)
    forbidden_returned = sorted(set(ranked) & set(case.get('forbidden_files', [])))
    return {
        'id': case['id'], 'role': case['role'], 'method': method,
        'question': case['question'],
        'project_code': case.get('project_code'),
        'relevant_files': case['relevant_files'],
        'ranked_filenames': ranked,
        'recall_at_k': recall_at_k(ranked, case['relevant_files'], k),
        'reciprocal_rank_at_k': reciprocal_rank_at_k(ranked, case['relevant_files'], k),
        'forbidden_returned': forbidden_returned,
        'expected_empty': bool(case.get('expected_empty', False)),
        'latency_ms': latency_ms,
    }


def markdown_report(metadata, scores, records) -> str:
    lines = [
        '# Asteria Studio — Retrieval Pilot Evaluation', '',
        '**Synthetic, three-document demo corpus; NOT a production-scale accuracy benchmark.**',
        f"Run (UTC): {metadata['generated_at_utc']}",
        f"Queries: {metadata['queries']} | Top K: {metadata['top_k']} | Corpus: {metadata['corpus']}", '',
        '| Retrieval | Doc Recall@K | Doc MRR@K | p50 (ms) | p95 (ms) | Forbidden exposures | Empty-result violations |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for method, s in scores.items():
        fmt = lambda v: f'{v:.4f}' if isinstance(v, float) else ('N/A' if v is None else str(v))
        lines.append(f"| {method} | {fmt(s['mean_document_recall_at_k'])} | {fmt(s['mrr_at_k'])} | {fmt(s['p50_latency_ms'])} | {fmt(s['p95_latency_ms'])} | {s['forbidden_document_exposures']} | {s['expected_empty_violations']} |")
    lines += [
        '', '## Interpretation and limitations',
        '- Document-level relevance was manually labeled; multiple chunks from the same document count once for Recall@K.',
        '- MRR@K is based on the rank of the first relevant *chunk* mapped to its source document.',
        '- Queries with no labeled accessible document are excluded from Recall and MRR averages; access checks are reported separately.',
        '- Warm-model local timing measures retrieval calls, not end-to-end Groq answer time. This run does not test answer faithfulness.',
        '- The corpus contains only three synthetic documents. No generalization or superiority claim should be made from this pilot.',
        '- These local demo identities are spoofable by anyone with the dev API key; this is not production authentication.',
        '', '## Case-by-case results', '',
        '| Case | Role | Method | Recall | RR | Latency (ms) | Forbidden exposure |',
        '|---|---|---|---:|---:|---:|---|',
    ]
    for r in records:
        a = 'N/A' if r['recall_at_k'] is None else f"{r['recall_at_k']:.2f}"
        b = 'N/A' if r['reciprocal_rank_at_k'] is None else f"{r['reciprocal_rank_at_k']:.2f}"
        lines.append(f"| {r['id']} | {r['role']} | {r['method']} | {a} | {b} | {r['latency_ms']} | {', '.join(r['forbidden_returned']) or 'none'} |")
    return '\n'.join(lines) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=DEFAULT_CASES)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--case-id', help='Run one labeled case first, e.g. Q01')
    args = parser.parse_args()
    if not 1 <= args.top_k <= 10:
        parser.error('--top-k must be between 1 and 10')
    cases = json.loads(args.cases.read_text(encoding='utf-8'))
    if args.case_id:
        cases = [case for case in cases if case['id'] == args.case_id]
        if not cases:
            parser.error(f'Unknown case ID {args.case_id}')
    for case in cases:
        if case['role'] not in DEMO_USERS:
            parser.error(f"Unknown demo role in case {case['id']}")

    print('Warming local embedding and reranker models (excluded from latency)...', flush=True)
    _ = embed_texts(['hotel upholstery fire dossier supplier quotation'])[0]
    _ = score_passages('hotel upholstery', ['Fictional hotel upholstery document'])
    methods = {'keyword': keyword_only, 'vector': vector_only, 'hybrid_rrf_rerank': hybrid}
    records = []
    with SessionLocal() as db:
        count = db.scalar(select(func.count()).select_from(Document).where(Document.status == 'ready'))
        for case in cases:
            for method, fn in methods.items():
                record = run_case(db, case, args.top_k, method, fn)
                records.append(record)
                print(f"{case['id']} {case['role']:<19} {method:<18} {record['latency_ms']:>7.1f} ms", flush=True)
    scores = {method: summarize(records, method) for method in methods}
    metadata = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'python': platform.python_version(),
        'top_k': args.top_k, 'queries': len(cases), 'corpus': f'{count} ready documents (across all tenants)',
        'measurement': 'warm-model retrieval only; document-level gold labels',
    }
    payload = {'metadata': metadata, 'summary': scores, 'cases': records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    report_path = args.output.with_suffix('.md')
    report_path.write_text(markdown_report(metadata, scores, records), encoding='utf-8')
    print(f'\nJSON: {args.output}\nReport: {report_path}')
    for method, score in scores.items():
        print(method, score)
    violations = sum(x['forbidden_document_exposures'] + x['expected_empty_violations'] for x in scores.values())
    if violations:
        print('\nFAIL: possible document authorization leakage in benchmark results')
        return 1
    print('\nPASS: no forbidden document exposures in tested retrieval cases')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
