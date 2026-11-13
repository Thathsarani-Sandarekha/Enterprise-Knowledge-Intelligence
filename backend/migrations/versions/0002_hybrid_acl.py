"""Role grants and indexed full-text retrieval for Task 4.

Revision ID: 0002_hybrid_acl
Revises: 0001_documents_chunks
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_hybrid_acl'
down_revision = '0001_documents_chunks'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'document_grants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(40), nullable=False),
        sa.UniqueConstraint('document_id', 'role', name='uq_document_grant_role'),
    )
    op.create_index('ix_document_grants_tenant_role', 'document_grants', ['tenant_id', 'role'])
    # Existing Task 3 demo documents are made visible to all fictional team roles.
    # Review these grants before ever migrating private/real-world documents.
    op.execute("""
    INSERT INTO document_grants (id, tenant_id, document_id, role)
    SELECT md5(d.id || ':' || v.role), d.tenant_id, d.id, v.role
    FROM documents AS d
    CROSS JOIN (VALUES ('designer'), ('procurement'), ('project_manager')) AS v(role)
    """)
    op.execute("""
    CREATE INDEX IF NOT EXISTS ix_chunks_text_fts
    ON document_chunks USING gin (to_tsvector('english'::regconfig, text))
    """)


def downgrade():
    op.execute('DROP INDEX IF EXISTS ix_chunks_text_fts')
    op.drop_index('ix_document_grants_tenant_role', table_name='document_grants')
    op.drop_table('document_grants')
