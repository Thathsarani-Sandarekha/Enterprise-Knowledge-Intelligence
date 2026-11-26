"""Run separately with RUN_DB_TESTS=1 after applying migration 0002.
Uses temporary *test-only documents* in your configured local database and
always deletes them in cleanup. Never run against a production DB.
"""
import os
from uuid import uuid4
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv('RUN_DB_TESTS') != '1',
    reason='Optional database integration test (set RUN_DB_TESTS=1)',
)


def test_tenant_and_role_filters_with_real_postgres():
    from sqlalchemy import select
    from app.database import SessionLocal
    from app.models import Document, DocumentGrant
    from app.routes.principals import DEMO_USERS
    from app.services.access import authorized_document_filter

    docs = []
    with SessionLocal() as session:
        try:
            for label, principal_id, roles in [
                ('public-to-design', 'aster-admin', ['designer']),
                ('private-to-procurement', 'aster-admin', ['procurement']),
                ('other-tenant', 'rival-admin', ['designer']),
            ]:
                principal = DEMO_USERS[principal_id]
                uid = str(uuid4())
                doc = Document(
                    id=uid, tenant_id=principal.tenant_id,
                    original_filename=f'{label}.pdf', stored_name=f'{uid}.pdf',
                    sha256=uuid4().hex * 2, media_type='application/pdf',
                    status='ready', project_code='ACL-TEST', chunk_count=0,
                )
                session.add(doc)
                session.flush()
                for role in roles:
                    session.add(DocumentGrant(tenant_id=principal.tenant_id, document_id=uid, role=role))
                docs.append(uid)
            session.flush()
            aster_design = set(session.scalars(select(Document.id).where(
                authorized_document_filter(DEMO_USERS['aster-designer']),
                Document.id.in_(docs))).all())
            aster_procure = set(session.scalars(select(Document.id).where(
                authorized_document_filter(DEMO_USERS['aster-procurement']),
                Document.id.in_(docs))).all())
            rival_design = set(session.scalars(select(Document.id).where(
                authorized_document_filter(DEMO_USERS['rival-designer']),
                Document.id.in_(docs))).all())
            assert aster_design == {docs[0]}
            assert aster_procure == {docs[1]}
            assert rival_design == {docs[2]}
        finally:
            session.rollback()  # Test does not persist its fixture documents
