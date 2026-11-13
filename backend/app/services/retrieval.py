"""Permission-filtered PostgreSQL FTS + pgvector + RRF + cross-encoder.

SQL-side tenant AND role filters appear in both search branches. No evidence
from other tenants or ungranted documents enters reranking or the LLM.
"""
from dataclasses import dataclass
import re
from time import perf_counter
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from app.models import Document, DocumentChunk
from app.routes.principals import Principal
from app.services.access import authorized_document_filter
from app.services.embeddings import embed_texts
from app.services.fusion import fused_ids, rrf_scores
from app.services.reranking import score_passages

STOP_WORDS = frozenset('find show tell which what where when who for our the and with from about including previous me please documents information approved project projects have were are a an of in to'.split())


def keyword_expression(question: str) -> str:
    tokens = re.findall(r'[A-Za-z][A-Za-z0-9]*|[0-9]+', question.lower())
    tokens = list(dict.fromkeys(t for t in tokens if (len(t) >= 2 or t.isdigit()) and t not in STOP_WORDS))
    return ' | '.join(tokens[:12])


@dataclass(frozen=True)
class Evidence:
    chunk_id: str
    document_id: str
    filename: str
    project_code: str | None
    text: str
    source: dict
    rrf_score: float
    rerank_score: float

    def as_dict(self) -> dict:
        return {
            'chunk_id': self.chunk_id,
            'document_id': self.document_id,
            'filename': self.filename,
            'project_code': self.project_code,
            'text': self.text,
            'source': self.source,
            'rrf_score': round(self.rrf_score, 6),
            'rerank_score': round(self.rerank_score, 4),
        }


def retrieve(
    db: Session,
    principal: Principal,
    question: str,
    *,
    project_code: str | None = None,
    top_k: int = 5,
    candidate_k: int = 20,
) -> tuple[list[Evidence], dict]:
    start = perf_counter()
    if not 1 <= top_k <= 10 or not top_k <= candidate_k <= 40:
        raise ValueError('Invalid search limits')

    shared_predicates = [
        DocumentChunk.tenant_id == principal.tenant_id,
        Document.status == 'ready',
        authorized_document_filter(principal),
    ]
    if project_code:
        shared_predicates.append(Document.project_code == project_code)

    attrs = (DocumentChunk, Document.original_filename, Document.project_code)
    query_vector = embed_texts([question])[0]
    cosine_distance = DocumentChunk.embedding.cosine_distance(query_vector)
    vector_rows = db.execute(
        select(*attrs)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(*shared_predicates)
        .order_by(cosine_distance.asc(), DocumentChunk.id)
        .limit(candidate_k)
    ).all()
    lexical = keyword_expression(question)
    if lexical:
        vector_of_terms = func.to_tsvector('english', DocumentChunk.text)
        tsquery = func.to_tsquery('english', lexical)
        rank = func.ts_rank_cd(vector_of_terms, tsquery)
        keyword_rows = db.execute(
            select(*attrs)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(*shared_predicates, vector_of_terms.op('@@')(tsquery))
            .order_by(desc(rank), DocumentChunk.id)
            .limit(candidate_k)
        ).all()
    else:
        keyword_rows = []

    candidates = {}
    for chunk, filename, project in [*vector_rows, *keyword_rows]:
        candidates[chunk.id] = (chunk, filename, project)
    lists = [
        [chunk.id for chunk, _, _ in keyword_rows],
        [chunk.id for chunk, _, _ in vector_rows],
    ]
    scores = rrf_scores(lists)
    fused = fused_ids(lists)[:candidate_k]
    if not fused:
        return [], {'keyword_candidates': 0, 'vector_candidates': 0,
                    'reranked': False, 'latency_ms': round(1000 * (perf_counter() - start), 1)}
    passages = [candidates[chunk_id][0].text for chunk_id in fused]
    rerank_scores = score_passages(question, passages)
    if len(rerank_scores) != len(fused):
        raise RuntimeError('Reranker returned incorrect score count')
    order = sorted(range(len(fused)), key=lambda i: (-rerank_scores[i], -scores[fused[i]], fused[i]))
    result = []
    for i in order[:top_k]:
        chunk, filename, project = candidates[fused[i]]
        result.append(Evidence(
            chunk_id=chunk.id, document_id=chunk.document_id,
            filename=filename, project_code=project,
            text=chunk.text, source=chunk.source_meta,
            rrf_score=scores[fused[i]], rerank_score=rerank_scores[i],
        ))
    return result, {
        'keyword_candidates': len(keyword_rows),
        'vector_candidates': len(vector_rows),
        'reranked': True,
        'latency_ms': round(1000 * (perf_counter() - start), 1),
        'note': 'Rerank scores are model logits, not confidence probabilities',
    }
