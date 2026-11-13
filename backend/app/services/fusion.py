"""Deterministic, pure Reciprocal Rank Fusion - easy to unit test."""


def rrf_scores(lists: list[list[str]], k: int = 60) -> dict[str, float]:
    if k <= 0:
        raise ValueError('RRF k must be positive')
    scores: dict[str, float] = {}
    for ranked_ids in lists:
        for rank, chunk_id in enumerate(dict.fromkeys(ranked_ids), 1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (k + rank)
    return scores


def fused_ids(lists: list[list[str]], k: int = 60) -> list[str]:
    scores = rrf_scores(lists, k=k)
    return sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))
