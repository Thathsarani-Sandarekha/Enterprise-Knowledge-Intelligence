"""Read-only smoke checks for Asteria Studio's LOCAL demo API.

Run from backend/ after starting FastAPI and PostgreSQL:
    python scripts/smoke_release.py
    python scripts/smoke_release.py --answers

Only synthetic demo identities and documents are used. The script does not
change the database or print secret API keys or document contents.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from time import perf_counter

import httpx
from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND / '.env')
BASE_URL = os.getenv('SMOKE_API_URL', 'http://127.0.0.1:8000').rstrip('/')
API_KEY = os.getenv('DEV_API_KEY', '')
FRONTEND_URL = os.getenv('SMOKE_FRONTEND_URL', 'http://127.0.0.1:3000').rstrip('/')
DOCS = {
    'synthetic_finish_approvals.docx',
    'synthetic_fire_document_register.pdf',
    'synthetic_supplier_quotes.xlsx',
}
QUOTES = 'synthetic_supplier_quotes.xlsx'
USERS = [
    'aster-admin', 'aster-procurement', 'aster-designer', 'aster-pm',
    'rival-designer', 'rival-admin',
]
QUESTION = (
    'Find the fire-rated upholstery materials approved for previous luxury hotel '
    'renovations, including supplier information and quoted prices.'
)


def request(client: httpx.Client, method: str, endpoint: str, user: str, **kwargs):
    start = perf_counter()
    response = client.request(
        method, f'{BASE_URL}{endpoint}',
        headers={'x-api-key': API_KEY, 'x-demo-user': user}, **kwargs,
    )
    elapsed_ms = (perf_counter() - start) * 1000
    if response.status_code != 200:
        raise AssertionError(f'{user} {endpoint}: HTTP {response.status_code}')
    return response.json(), elapsed_ms


def verify_lists(client: httpx.Client) -> None:
    print('\n[1] Document listing and access isolation')
    for user in USERS:
        print(f"Checking documents for {user}...", flush=True)
        data, elapsed = request(client, 'GET', '/api/v1/documents', user)
        assert isinstance(data, list), f'{user}: expected list'
        names = {doc.get('filename') for doc in data}
        if user in ('aster-admin', 'aster-procurement'):
            assert DOCS <= names, f'{user}: missing one or more demo documents'
        elif user in ('aster-designer', 'aster-pm'):
            assert QUOTES not in names, f'{user}: restricted quote workbook leaked'
            assert (DOCS - {QUOTES}) <= names, f'{user}: missing design documents'
        else:
            assert not (DOCS & names), f'{user}: cross-tenant document leak'
        if user == 'aster-admin':
            docs = {doc['filename']: doc for doc in data}
            for name in DOCS:
                assert docs[name]['status'] == 'ready', f'{name} not ready'
        print(f'  PASS {user:20} visible={len(data):2} list_latency={elapsed:.0f} ms')


def verify_answers(client: httpx.Client) -> None:
    print('\n[2] Live Groq answers and access isolation (optional, uses API tokens)')
    for user in ('aster-procurement', 'aster-designer', 'rival-designer'):
        data, elapsed = request(
            client, 'POST', '/api/v1/knowledge/ask', user,
            json={'question': QUESTION, 'top_k': 6},
            timeout=120,
        )
        answer = str(data.get('answer', ''))
        citations = data.get('citations', [])
        if user == 'aster-procurement':
            assert data.get('status') == 'answered', 'Procurement answer abstained'
            assert '145' in answer and '189' in answer, 'Missing expected synthetic prices'
            assert any(c.get('filename') == QUOTES for c in citations), 'Workbook citation missing'
        elif user == 'aster-designer':
            assert '145' not in answer and '189' not in answer, 'Restricted prices leaked'
            assert all(c.get('filename') != QUOTES for c in citations), 'Restricted citation leaked'
        else:
            assert data.get('status') == 'insufficient_evidence', 'Unexpected other-tenant answer'
            assert not citations, 'Other tenant received a citation'
        print(f'  PASS {user:20} status={data.get("status")} latency={elapsed:.0f} ms')


def verify_gateway(client: httpx.Client) -> None:
    print('\n[3] Next.js API gateway (requires running frontend)')
    start = perf_counter()
    response = client.get(
        f'{FRONTEND_URL}/api/gateway/documents',
        headers={'x-demo-user': 'aster-admin'}, timeout=30,
    )
    ms = (perf_counter() - start) * 1000
    assert response.status_code == 200, f'Gateway returned HTTP {response.status_code}'
    data = response.json()
    assert isinstance(data, list), 'Gateway response is not a document list'
    names = {doc.get('filename') for doc in data}
    assert DOCS <= names, 'Gateway response does not contain all three hotel documents'
    print(f'  PASS admin documents={len(data)} gateway_latency={ms:.0f} ms')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--answers', action='store_true', help='also make real Groq calls')
    parser.add_argument('--gateway', action='store_true', help='also verify Next.js gateway (frontend must be running)')
    args = parser.parse_args()
    if not API_KEY:
        print('FAIL: DEV_API_KEY not set in backend/.env', file=sys.stderr)
        return 2
    try:
        with httpx.Client(timeout=15, trust_env=False) as client:
            verify_lists(client)
            if args.answers:
                verify_answers(client)
            if args.gateway:
                verify_gateway(client)
    except (httpx.HTTPError, AssertionError, ValueError) as exc:
        print(f'FAIL: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1
    print('\nPASS: All selected local smoke checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
