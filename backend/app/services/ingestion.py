"""A durable, database-queued local worker. Status survives API restarts."""
import logging
from pathlib import Path
from sqlalchemy import select
from app.config import STORAGE_DIR
from app.database import SessionLocal
from app.models import Document, DocumentChunk
from app.services.embeddings import embed_texts
from app.services.extraction import extract_document
from app.services.object_storage import materialized_document

logger = logging.getLogger(__name__)


def claim_next_document() -> str | None:
    with SessionLocal.begin() as db:
        document = db.scalars(
            select(Document)
            .where(Document.status == 'queued')
            .order_by(Document.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        ).first()
        if document is None:
            return None
        document.status = 'processing'
        return document.id


def process_claimed_document(document_id: str) -> None:
    with SessionLocal() as db:
        document = db.get(Document, document_id)
        if document is None or document.status != 'processing':
            return
        stored_ref = document.stored_name
        tenant_id = document.tenant_id
    try:
        with materialized_document(stored_ref, tenant_id) as storage_path:
            fragments = extract_document(storage_path)
        embeddings = embed_texts([fragment.text for fragment in fragments])
        with SessionLocal.begin() as db:
            document = db.get(Document, document_id, with_for_update=True)
            if document is None or document.status != 'processing':
                raise RuntimeError('Document processing state unexpectedly changed')
            db.add_all([
                DocumentChunk(
                    tenant_id=tenant_id,
                    document_id=document_id,
                    chunk_index=i,
                    text=fragment.text,
                    source_meta=fragment.source_meta,
                    embedding=embeddings[i],
                )
                for i, fragment in enumerate(fragments)
            ])
            document.chunk_count = len(fragments)
            document.status = 'ready'
            document.error_code = None
        logger.info('Indexed document id=%s chunks=%d', document_id, len(fragments))
    except Exception as exc:
        # Never log extracted contents, traceback paths, or document text.
        logger.error('Indexing failed document id=%s exception_type=%s', document_id, type(exc).__name__)
        with SessionLocal.begin() as db:
            document = db.get(Document, document_id, with_for_update=True)
            if document is not None:
                document.status = 'failed'
                document.error_code = type(exc).__name__[:60]
