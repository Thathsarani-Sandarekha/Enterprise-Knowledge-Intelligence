"""Tenant-scoped initial document and evidence schema.

There is no real user authorization. The API is local-only.
"""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import VECTOR


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = 'documents'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'sha256', name='uq_documents_tenant_sha'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    media_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='queued')
    project_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class DocumentChunk(Base):
    __tablename__ = 'document_chunks'
    __table_args__ = (
        UniqueConstraint('document_id', 'chunk_index', name='uq_chunks_document_index'),
        Index('ix_chunks_tenant_document', 'tenant_id', 'document_id'),
        Index('ix_chunks_embedding_hnsw', 'embedding', postgresql_using='hnsw',
              postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source_meta: Mapped[dict] = mapped_column(JSONB, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(VECTOR(384), nullable=False)

class DocumentGrant(Base):
    """Document-level access grant for a role in the document's tenant.

    A grant to 'designer' does NOT imply access for 'procurement'. Admin
    access is defined by the trusted principal mapping, not this table.
    """
    __tablename__ = 'document_grants'
    __table_args__ = (
        UniqueConstraint('document_id', 'role', name='uq_document_grant_role'),
        Index('ix_document_grants_tenant_role', 'tenant_id', 'role'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False
    )
    role: Mapped[str] = mapped_column(String(40), nullable=False)
