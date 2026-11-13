"""Local cross-encoder; CPU inference, never interprets scores as probabilities."""
from functools import lru_cache
from sentence_transformers import CrossEncoder

MODEL_NAME = 'cross-encoder/ms-marco-MiniLM-L-6-v2'


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    return CrossEncoder(MODEL_NAME, device='cpu')


def score_passages(question: str, passages: list[str]) -> list[float]:
    if not passages:
        return []
    pairs = [(question, passage[:2400]) for passage in passages]
    raw = get_reranker().predict(pairs, batch_size=8, show_progress_bar=False)
    return [float(v) for v in raw]
