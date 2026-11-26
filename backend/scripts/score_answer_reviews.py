"""Score manually audited factual claims; no LLM judge and no invented values.

Run (after editing all review objects you want scored):
python scripts/score_answer_reviews.py
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = BACKEND / 'evaluation' / 'results' / 'answer_quality_review_template.json'
DEFAULT_OUTPUT = BACKEND / 'evaluation' / 'results' / 'answer_quality_manual_review.json'


def score_manual_reviews(reviews: list[dict]) -> dict:
    selected = [r for r in reviews if r.get('reviewed') is True]
    total_claims = 0
    supported = 0
    citation_supported = 0
    correct_cases = 0
    for row in selected:
        if not isinstance(row.get('overall_correct'), bool):
            raise ValueError(f"{row.get('id')}: overall_correct must be true or false when reviewed")
        correct_cases += row['overall_correct']
        if not isinstance(row.get('claims'), list):
            raise ValueError(f"{row.get('id')}: claims must be a list")
        if row.get('response_status') == 'answered' and not row['claims']:
            raise ValueError(f"{row.get('id')}: answered responses require atomic claim annotations")
        for claim in row['claims']:
            if (not isinstance(claim.get('claim'), str) or not claim['claim'].strip() or
                    not isinstance(claim.get('supported'), bool) or
                    not isinstance(claim.get('citation_supports'), bool)):
                raise ValueError(f"{row.get('id')}: each claim requires text, supported bool and citation_supports bool")
            total_claims += 1
            supported += claim['supported']
            citation_supported += claim['citation_supports']
    r = lambda n, d: round(n / d, 4) if d else None
    return {
        'reviewed_cases': len(selected),
        'unreviewed_cases': len(reviews) - len(selected),
        'case_level_answer_correctness_reviewed': r(correct_cases, len(selected)),
        'claims_audited': total_claims,
        'claim_level_faithfulness_reviewed': r(supported, total_claims),
        'unsupported_claim_count': total_claims - supported,
        'unsupported_claim_rate_reviewed': r(total_claims - supported, total_claims),
        'claim_level_citation_support_reviewed': r(citation_supported, total_claims),
        'note': 'Human-reviewed, synthetic-corpus pilot; rates cover reviewed cases/claims only.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reviews', type=Path, default=DEFAULT_REVIEW)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    data = json.loads(args.reviews.read_text(encoding='utf-8'))
    score = score_manual_reviews(data['reviews'])
    output = {'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'manual_review': score}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    md_lines = [
        '# Asteria Studio — Manual Answer Quality Audit', '',
        f"Reviewed cases: {score['reviewed_cases']} / {len(data['reviews'])}",
        f"Atomic factual claims reviewed: {score['claims_audited']}",
        '', '| Metric | Value |', '|---|---:|',
    ]
    for key in ('case_level_answer_correctness_reviewed', 'claim_level_faithfulness_reviewed',
                'unsupported_claim_count', 'unsupported_claim_rate_reviewed',
                'claim_level_citation_support_reviewed'):
        v = score[key]
        md_lines.append(f"| {key} | {'not measured' if v is None else v} |")
    md_lines += ['', 'These are human-annotated case/claim metrics, not automated LLM judge results.',
                 'If the review is incomplete, do not present these as scores for the entire dataset.', '']
    args.output.with_suffix('.md').write_text('\n'.join(md_lines), encoding='utf-8')
    print(json.dumps(score, indent=2))
    print('Report:', args.output.with_suffix('.md'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
