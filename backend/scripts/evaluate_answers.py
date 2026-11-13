"""Read-only live RAG-answer quality pilot (Asteria Studio synthetic corpus).

From backend/: python scripts/evaluate_answers.py --case-id A01
Then:           python scripts/evaluate_answers.py

Calls Groq via FastAPI's existing endpoint; costs provider tokens. Does not
upload/delete documents, alter grants, or overwrite application code.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from time import perf_counter

import httpx
from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from evaluation.answer_quality_metrics import evaluate_response, summarize

load_dotenv(BACKEND / '.env')
DEFAULT_CASES = BACKEND / 'evaluation' / 'answer_quality_cases.json'
DEFAULT_OUTPUT = BACKEND / 'evaluation' / 'results' / 'answer_quality_pilot.json'
DEFAULT_API = os.environ.get('SMOKE_API_URL', 'http://127.0.0.1:8000').rstrip('/')


def markdown_summary(payload: dict) -> str:
    s = payload['summary']
    fmt = lambda v: 'not measured' if v is None else (f'{v:.4f}' if isinstance(v, float) else str(v))
    out = [
        '# Asteria Studio — B3 Answer Quality Pilot', '',
        '**Synthetic 3-document corpus; preliminary local evaluation. Not production validation.**',
        f"UTC: {payload['generated_at_utc']}",
        f"Model requested: `{payload['configured_groq_model']}`",
        f"Cases executed: {s['cases_requested']}; responses: {s['api_responses_received']}; errors: {s['api_errors']}",
        '', '## Automatically measured signals', '',
        '| Signal | Result |', '|---|---:|',
    ]
    metric_labels = {
        'automatic_case_pass_rate': 'Reference-fact / source / status rule pass rate',
        'reference_fact_match_rate_answerable_cases': 'Reference fact pattern coverage (not semantic correctness)',
        'abstention_precision_on_labeled_full_abstention_cases': 'Full-abstention precision',
        'abstention_recall_on_labeled_full_abstention_cases': 'Full-abstention recall',
        'forbidden_citation_source_exposures': 'Forbidden citation-source exposures',
        'forbidden_answer_pattern_exposures': 'Forbidden answer-pattern exposures',
        'latency_p50_ms': 'Full API latency p50 (ms)',
        'latency_p95_ms': 'Full API latency p95 (ms)',
        'reported_input_tokens_sum': 'Input tokens reported by API (partial possible)',
        'reported_output_tokens_sum': 'Output tokens reported by API (partial possible)',
        'responses_missing_token_usage': 'Responses lacking token counts',
        'exact_total_provider_cost_usd': 'Exact provider cost (USD)',
    }
    for key, label in metric_labels.items():
        out.append(f'| {label} | {fmt(s.get(key))} |')
    out.extend(['', '## Per-case evidence', '',
                '| ID | Role | Kind | API status | Automatic checks | Facts | Cites | Latency (ms) |',
                '|---|---|---|---|---|---|---:|---:|'])
    for r in payload['cases']:
        a = r['automatic']
        status = a.get('status') or r.get('error_type') or 'error'
        fact = f"{a['reference_facts_matched']}/{a['reference_facts_total']}" if a['reference_facts_total'] else '-'
        out.append(f"| {r['id']} | {r['role']} | {r['kind']} | {status} | {'PASS' if a['passed_automatic_checks'] else 'CHECK'} | {fact} | {a['citation_count']} | {fmt(r.get('latency_ms'))} |")
    out.extend([
        '', '## What is NOT measured automatically', '',
        '- **Answer correctness:** regex fact matches do not detect contradictory statements or unsupported extra claims.',
        '- **Faithfulness / hallucination rate:** requires claim-by-claim inspection against source evidence.',
        '- **Semantic citation accuracy:** `citation_integrity=passed` confirms real quotations, not whether cited text supports each answer claim.',
        '- **Price protection:** simple patterns and source filenames are screening checks, not a substitute for policy/security assessment.',
        '- **Cost:** Groq pricing is not assumed; some abstention responses omit token usage. Reported tokens may therefore be incomplete.',
        '- **Latency:** response time includes the server, retrieval, and Groq. Cold/warm model state and network conditions are not controlled across machines.',
        '', '## Required manual review', '',
        'Review original synthetic documents and all returned claims using `answer_quality_review_template.json`.',
        'Populate each case with atomic claims and whether evidence supports each claim and its citation.',
        'Run `python scripts/score_answer_reviews.py` after review to quantify faithfulness, semantic citation correctness,',
        'hallucinations and manual answer correctness. Keep those metrics labeled **not evaluated** until the review is done.',
        '', '## Baseline context', '',
        'B1 retrieval pilot: keyword MRR@5 0.8889; vector 0.6347; hybrid 0.8333, all on the same small 3-document corpus.',
        'B3 evaluates full answers, not retrieval ranking, so do not compare their latencies directly.',
        '',
    ])
    return '\n'.join(out)


def review_template(payload: dict) -> dict:
    return {
        '_instructions': [
            'Synthetic source records only. Do not use for private client documents.',
            'For each case, mark reviewed true only after inspecting output against original docs and authorized evidence.',
            'List EVERY atomic factual claim from the answer in claims, not just facts you expect to be true.',
            'supported means authorized source evidence entails the claim. citation_supports means an attached citation supports that claim.',
            'For insufficient_evidence, claims=[]; decide whether refusal is correct using the reference corpus.',
            'overall_correct should reflect the entire response, including omissions and unsupported facts.',
            'Never populate true values automatically. Unreviewed metrics must remain unreported.',
        ],
        'reviews': [
            {
                'id': row['id'],
                'role': row['role'],
                'question': row['question'],
                'response_status': (row['response'] or {}).get('status'),
                'response_answer': (row['response'] or {}).get('answer'),
                'response_citations': (row['response'] or {}).get('citations', []),
                'reviewed': False,
                'overall_correct': None,
                'claims': [],
                'notes': '',
            }
            for row in payload['cases']
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-id', help='Single labeled case, e.g. A01')
    parser.add_argument('--limit', type=int, help='Run only first N cases as a quick smoke test')
    parser.add_argument('--cases', type=Path, default=DEFAULT_CASES)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--api-url', default=DEFAULT_API)
    parser.add_argument('--top-k', type=int, default=6)
    parser.add_argument('--warm-models', action='store_true', help='Warm retrieval using /search (no LLM) before measured cases')
    args = parser.parse_args()
    if not (1 <= args.top_k <= 10):
        parser.error('--top-k must be 1..10')
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    if not os.environ.get('DEV_API_KEY'):
        parser.error('DEV_API_KEY is missing from backend/.env')

    cases = json.loads(args.cases.read_text(encoding='utf-8'))
    if args.case_id:
        cases = [c for c in cases if c['id'] == args.case_id]
        if not cases:
            parser.error(f'Unknown case id: {args.case_id}')
    if args.limit:
        cases = cases[:args.limit]

    rows = []
    with httpx.Client(timeout=httpx.Timeout(connect=5, read=120, write=15, pool=5), trust_env=False) as client:
        if args.warm_models:
            first = cases[0]
            print('Warming FastAPI retrieval models via /knowledge/search (no Groq call)...', flush=True)
            warm = client.post(args.api_url.rstrip('/') + '/api/v1/knowledge/search',
                               headers={'x-api-key': os.environ['DEV_API_KEY'], 'x-demo-user': first['role']},
                               json={'question': first['question'], 'top_k': args.top_k})
            warm.raise_for_status()
        for case in cases:
            headers = {'x-api-key': os.environ['DEV_API_KEY'], 'x-demo-user': case['role']}
            body = {'question': case['question'], 'top_k': args.top_k}
            if case.get('project_code'):
                body['project_code'] = case['project_code']
            start = perf_counter()
            try:
                result = client.post(args.api_url.rstrip('/') + '/api/v1/knowledge/ask', headers=headers, json=body)
                result.raise_for_status()
                data = result.json()
                elapsed = round((perf_counter() - start) * 1000, 1)
                automatic = evaluate_response(case, data)
                row = {
                    'id': case['id'], 'role': case['role'], 'kind': case['kind'],
                    'question': case['question'], 'response': data,
                    'automatic': automatic, 'latency_ms': elapsed,
                }
            except (httpx.HTTPError, ValueError) as exc:
                elapsed = round((perf_counter() - start) * 1000, 1)
                row = {
                    'id': case['id'], 'role': case['role'], 'kind': case['kind'],
                    'question': case['question'], 'response': None,
                    'automatic': evaluate_response(case, None), 'latency_ms': elapsed,
                    'error_type': type(exc).__name__,
                    'http_status': exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None,
                }
            rows.append(row)
            auto = row['automatic']
            print(f"{'PASS' if auto['passed_automatic_checks'] else 'CHECK'} {case['id']} {case['role']:<20} "
                  f"{auto['status'] or row.get('error_type') or '-':<24} "
                  f"{row['latency_ms']:>8.1f} ms", flush=True)

    payload = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'api_url': args.api_url.rstrip('/'),
        'configured_groq_model': os.environ.get('GROQ_MODEL', 'openai/gpt-oss-20b'),
        'corpus': 'three synthetic Asteria Studio hospitality documents',
        'cases': rows,
        'summary': summarize(cases, rows),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    md = args.output.with_suffix('.md')
    md.write_text(markdown_summary(payload) + '\n', encoding='utf-8')
    review = args.output.parent / 'answer_quality_review_template.json'
    review.write_text(json.dumps(review_template(payload), indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Results:', args.output)
    print('Report:', md)
    print('Manual review template:', review)
    summary = payload['summary']
    print('Automatic pass rate:', summary['automatic_case_pass_rate'])
    print('Manual faithfulness, semantic citations and hallucinations: NOT YET MEASURED')
    # A proxy CHECK is flagged to invite review, not treated as a script runtime error.
    return 0 if not summary['api_errors'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
