"""Initial document and chunk tables.

Revision ID: 0001_documents_chunks
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import VECTOR

revision = '0001_documents_chunks'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.create_table(
        'documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('stored_name', sa.String(100), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('media_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('project_code', sa.String(80), nullable=True),
        sa.Column('chunk_count', sa.Integer(), nullable=False),
        sa.Column('error_code', sa.String(60), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'sha256', name='uq_documents_tenant_sha'),
    )
    op.create_index('ix_documents_tenant_id', 'documents', ['tenant_id'])
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('source_meta', JSONB(), nullable=False),
        sa.Column('embedding', VECTOR(384), nullable=False),
        sa.UniqueConstraint('document_id', 'chunk_index', name='uq_chunks_document_index'),
    )
    op.create_index('ix_chunks_tenant_document', 'document_chunks', ['tenant_id', 'document_id'])
    op.create_index('ix_chunks_embedding_hnsw', 'document_chunks', ['embedding'],
                    postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'})


def downgrade():
    op.drop_index('ix_chunks_embedding_hnsw', table_name='document_chunks')
    op.drop_index('ix_chunks_tenant_document', table_name='document_chunks')
    op.drop_table('document_chunks')
    op.drop_index('ix_documents_tenant_id', table_name='documents')
    op.drop_table('documents')
