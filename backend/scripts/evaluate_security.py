"""Asteria Studio read-only, local security smoke evaluation.

Run from backend/: python scripts/evaluate_security.py
Optional Groq calls: python scripts/evaluate_security.py --answers

Does not modify documents, grants, database, or model settings.
Identity headers are LOCAL DEMO ONLY and do not constitute authentication.
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
load_dotenv(BACKEND / '.env')

API = os.environ.get('SMOKE_API_URL', 'http://127.0.0.1:8000').rstrip('/')
OUTPUT = BACKEND / 'evaluation' / 'results' / 'security_smoke.json'
EXPECTED = {
    'aster-admin': 3,
    'aster-procurement': 3,
    'aster-designer': 2,
    'aster-pm': 2,
    'rival-designer': 0,
    'rival-admin': 0,
}
RESTRICTED_FILE = 'synthetic_supplier_quotes.xlsx'
ASTERA_FILES = {
    'synthetic_finish_approvals.docx',
    'synthetic_fire_document_register.pdf',
    'synthetic_supplier_quotes.xlsx',
}
QUESTION = (
    'Find approved fire-rated upholstery materials from luxury hotel projects, '
    'including supplier names and quoted prices.'
)
# Testing against known *fictional* fixture values; don't use with private data.
PRICE_MARKERS = ('145', '189')


def call(client: httpx.Client, method: str, path: str, role: str, **kwargs):
    headers = {'x-api-key': os.environ['DEV_API_KEY'], 'x-demo-user': role}
    start = perf_counter()
    res = client.request(method, f'{API}{path}', headers=headers, **kwargs)
    ms = round((perf_counter() - start) * 1000, 1)
    res.raise_for_status()
    return res.json(), ms


def safe_write(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    out = path.with_suffix('.md')
    rows = [
        '# Asteria Studio — Security Smoke Evaluation', '',
        '**Local demo identities are spoofable; this is not a production authentication or penetration test.**',
        f"Run (UTC): {payload['generated_at_utc']}",
        f"Base URL: {payload['base_url']}", '',
        '| Identity | Document count | Search evidence count | Forbidden source exposed | Result |',
        '|---|---:|---:|---|---|',
    ]
    for c in payload['access_checks']:
        rows.append(
            f"| {c['identity']} | {c['documents']} | {c['search_results']} | "
            f"{'yes' if c['forbidden_source_exposed'] else 'no'} | "
            f"{'PASS' if c['passed'] else 'FAIL'} |"
        )
    rows.extend(['', '## Optional model-answer checks', ''])
    if payload['answer_checks']:
        for c in payload['answer_checks']:
            rows.append(f"- {c['identity']}: {c['status']} — {'PASS' if c['passed'] else 'FAIL'}; {c['latency_ms']} ms")
    else:
        rows.append('- Not run (add `--answers` for Groq-dependent checks).')
    rows.extend([
        '', '## Limitations',
        '- Only three synthetic documents and six local demo identities were tested.',
        '- The negative checks exercise SQL-scoped retrieval and response behavior, not identity verification.',
        '- This does not test malicious content embedded in stored documents, production key handling, or parser sandboxing.',
        '- PII redaction in application logs and model responses is NOT established by this script.',
        '- Source existence and verbatim quote verification do not prove claim-level faithfulness.',
        '- Do not report zero prompt-injection success or zero PII leakage without dedicated evaluations.',
        '', f"Overall: **{'PASS' if payload['passed'] else 'FAIL'}**", '',
    ])
    out.write_text('\n'.join(rows), encoding='utf-8')
    print('JSON:', path)
    print('Report:', out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--answers', action='store_true', help='Run 3 live Groq answer checks (costs tokens)')
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    if not os.environ.get('DEV_API_KEY'):
        parser.error('Set DEV_API_KEY in backend/.env')

    checks = []
    answer_checks = []
    # Disabling automatic proxy inheritance mirrors the working local API test.
    with httpx.Client(timeout=httpx.Timeout(30.0), trust_env=False) as client:
        for role, expected_count in EXPECTED.items():
            print(f"[{role}] Checking document access...", flush=True)

            documents, list_ms = call(
                client, 'GET', '/api/v1/documents', role
            )

            print(
                f"[{role}] Documents OK ({list_ms} ms). "
                "Running hybrid search...",
                flush=True
            )

            search, search_ms = call(
                client,
                'POST',
                '/api/v1/knowledge/search',
                role,
                json={'question': QUESTION, 'top_k': 6}
            )

            print(
                f"[{role}] Search OK ({search_ms} ms)",
                flush=True
            )
            filenames = {x.get('filename') for x in search.get('results', [])}
            observed = len(documents)
            other_tenant = role.startswith('rival-')
            restricted_role = role in {'aster-designer', 'aster-pm'}
            forbidden = ((other_tenant and bool(filenames & ASTERA_FILES))
                         or (restricted_role and RESTRICTED_FILE in filenames))
            unexpected_docs = ((other_tenant and observed != 0)
                               or (restricted_role and any(
                                   d.get('filename') == RESTRICTED_FILE for d in documents)))
            passed = observed == expected_count and not forbidden and not unexpected_docs
            row = {
                'identity': role, 'documents': observed,
                'expected_documents': expected_count,
                'search_results': len(search.get('results', [])),
                'forbidden_source_exposed': bool(forbidden or unexpected_docs),
                'list_latency_ms': list_ms, 'search_latency_ms': search_ms,
                'passed': passed,
            }
            checks.append(row)
            print(f"{'PASS' if passed else 'FAIL'} {role:<19} docs={observed} "
                  f"search={row['search_results']} forbidden={row['forbidden_source_exposed']}", flush=True)

        if args.answers:
            for role in ('aster-procurement', 'aster-designer', 'rival-designer'):
                data, ms = call(client, 'POST', '/api/v1/knowledge/ask', role,
                                json={'question': QUESTION, 'top_k': 6})
                answer = data.get('answer', '')
                status = data.get('status')
                cites = data.get('citations') or []
                source_names = {c.get('filename') for c in cites}
                other_tenant = role.startswith('rival-')
                no_privileged = role == 'aster-designer' and (
                    RESTRICTED_FILE not in source_names and
                    all(p not in answer for p in PRICE_MARKERS)
                )
                if other_tenant:
                    passed = status == 'insufficient_evidence' and not cites
                elif role == 'aster-designer':
                    passed = status == 'answered' and bool(cites) and no_privileged
                else:
                    passed = (status == 'answered' and bool(cites) and
                              RESTRICTED_FILE in source_names and
                              all(p in answer for p in PRICE_MARKERS))
                answer_checks.append({'identity': role, 'status': status,
                                      'latency_ms': ms, 'citation_count': len(cites),
                                      'passed': passed})
                print(f"{'PASS' if passed else 'FAIL'} answer {role:<19} {status} {ms:.1f}ms", flush=True)

    payload = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'base_url': API,
        'corpus': 'three synthetic hospitality documents',
        'access_checks': checks, 'answer_checks': answer_checks,
        'passed': all(c['passed'] for c in [*checks, *answer_checks]),
    }
    safe_write(payload, args.output)
    return 0 if payload['passed'] else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        print(f'FAILED: {type(exc).__name__}: {str(exc)[:300]}', file=sys.stderr)
        raise SystemExit(2)
