"""Local sentence embeddings; Groq remains the LLM provider only."""
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_DIMS, EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL, device='cpu')


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = get_embedder().encode(
        texts,
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    output = vectors.tolist()
    if any(len(row) != EMBEDDING_DIMS for row in output):
        raise ValueError('Embedding model dimensions do not match VECTOR(384)')
    return output
