"""Document-level retrieval metrics; duplicate chunks cannot inflate recall."""
from __future__ import annotations
from math import ceil
from statistics import mean, median


def recall_at_k(ranked_filenames: list[str], relevant_filenames: list[str], k: int) -> float | None:
    if k < 1:
        raise ValueError('k must be positive')
    relevant = set(relevant_filenames)
    if not relevant:
        return None  # Unanswerable/access-denied probes are scored separately.
    return len(relevant.intersection(ranked_filenames[:k])) / len(relevant)


def reciprocal_rank_at_k(ranked_filenames: list[str], relevant_filenames: list[str], k: int) -> float | None:
    if k < 1:
        raise ValueError('k must be positive')
    relevant = set(relevant_filenames)
    if not relevant:
        return None
    for rank, filename in enumerate(ranked_filenames[:k], start=1):
        if filename in relevant:
            return 1 / rank
    return 0.0


def percentile_nearest_rank(numbers: list[float], p: float) -> float | None:
    if not numbers:
        return None
    if not 0 < p <= 1:
        raise ValueError('p must be in (0, 1]')
    ordered = sorted(numbers)
    return ordered[ceil(len(ordered) * p) - 1]


def summarize(records: list[dict], method: str) -> dict:
    selected = [record for record in records if record['method'] == method]
    scored = [r for r in selected if r['recall_at_k'] is not None]
    latencies = [r['latency_ms'] for r in selected]
    return {
        'queries': len(selected),
        'answerable_queries': len(scored),
        'access_probes': len(selected) - len(scored),
        'mean_document_recall_at_k': round(mean(r['recall_at_k'] for r in scored), 4) if scored else None,
        'mrr_at_k': round(mean(r['reciprocal_rank_at_k'] for r in scored), 4) if scored else None,
        'p50_latency_ms': round(median(latencies), 1) if latencies else None,
        'p95_latency_ms': round(percentile_nearest_rank(latencies, .95), 1) if latencies else None,
        'forbidden_document_exposures': sum(len(r['forbidden_returned']) for r in selected),
        'expected_empty_violations': sum(bool(r['expected_empty'] and r['ranked_filenames']) for r in selected),
    }
