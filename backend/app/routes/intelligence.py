"""Hybrid retrieval and grounded-QA API endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.routes.principals import Principal, get_demo_principal
from app.services.retrieval import retrieve
from app.services.answers import generate_answer

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/v1/knowledge', tags=['Knowledge Intelligence'])


class KnowledgeQuery(BaseModel):
    question: str = Field(min_length=5, max_length=500)
    project_code: str | None = Field(default=None, max_length=80, pattern=r'^[A-Za-z0-9_-]+$')
    top_k: int = Field(default=5, ge=1, le=10)


@router.post('/search')
def hybrid_search(
    request: KnowledgeQuery,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_demo_principal),
):
    try:
        evidence, stats = retrieve(
            db, principal, request.question,
            project_code=request.project_code, top_k=request.top_k,
        )
    except Exception as exc:
        logger.error('Hybrid retrieval failed; type=%s', type(exc).__name__)
        raise HTTPException(503, 'Retrieval service is unavailable') from exc
    return {'results': [chunk.as_dict() for chunk in evidence], 'retrieval': stats}


@router.post('/ask')
def ask_knowledge(
    request: KnowledgeQuery,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_demo_principal),
):
    try:
        evidence, stats = retrieve(
            db, principal, request.question,
            project_code=request.project_code, top_k=request.top_k,
        )
    except Exception as exc:
        logger.error('Retrieval failed; type=%s', type(exc).__name__)
        raise HTTPException(503, 'Retrieval service is unavailable') from exc
    try:
        return generate_answer(request.question, evidence, stats)
    except Exception as exc:
        logger.exception(
            "Answer generation failed: type=%s, status=%s",
            type(exc).__name__,
            getattr(exc, "status_code", "N/A"),
        )
        raise HTTPException(
            status_code=502,
            detail="LLM provider response unavailable",
        ) from exc
