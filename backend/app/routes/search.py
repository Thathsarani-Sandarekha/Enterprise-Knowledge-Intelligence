"""vector-only diagnostic endpoint with mandatory access checks."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document, DocumentChunk
from app.routes.principals import Principal, get_demo_principal
from app.services.access import authorized_document_filter
from app.services.embeddings import embed_texts

router = APIRouter(prefix='/api/v1/search', tags=['Search'])


class VectorSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)


@router.post('/vector')
def vector_search(
    request: VectorSearchRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_demo_principal),
):
    vector = embed_texts([request.query])[0]
    distance = DocumentChunk.embedding.cosine_distance(vector)
    rows = db.execute(
        select(DocumentChunk, Document.original_filename, distance.label('distance'))
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(DocumentChunk.tenant_id == principal.tenant_id,
               Document.status == 'ready',
               authorized_document_filter(principal))
        .order_by(distance)
        .limit(request.top_k)
    ).all()
    return {
        'query': request.query,
        'results': [
            {
                'chunk_id': chunk.id, 'document_id': chunk.document_id,
                'filename': filename, 'text': chunk.text,
                'source': chunk.source_meta, 'distance': float(d),
            }
            for chunk, filename, d in rows
        ],
        'note': 'Vector diagnostic with tenant/role filtering; use /knowledge/search for hybrid retrieval',
    }
