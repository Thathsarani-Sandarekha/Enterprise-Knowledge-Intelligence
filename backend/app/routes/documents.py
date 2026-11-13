"""Tenant/role-aware local-demo document endpoints.

Uploads and permission changes are demo-admin only. The 'x-demo-user' header
is only a simulator and MUST be replaced with real authentication for production.
"""
import hashlib
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.config import MAX_UPLOAD_BYTES, STORAGE_DIR
from app.database import get_db
from app.models import Document, DocumentGrant
from app.routes.principals import Principal, get_demo_principal, require_demo_admin
from app.services.access import authorized_document_filter, validate_roles
from app.services.validation import inspect_upload
from app.services.object_storage import generate_reference, store_bytes, best_effort_delete

router = APIRouter(prefix='/api/v1/documents', tags=['Documents'])


def serialize(doc: Document) -> dict:
    return {
        'id': doc.id, 'filename': doc.original_filename,
        'project_code': doc.project_code, 'status': doc.status,
        'chunk_count': doc.chunk_count, 'error_code': doc.error_code,
        'created_at': doc.created_at.isoformat(),
    }


@router.post('', status_code=202)
def upload_document(
    file: UploadFile = File(...),
    project_code: str | None = None,
    allowed_roles: str = Form(default='designer,procurement,project_manager'),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_demo_admin),
):
    try:
        roles = validate_roles(allowed_roles.split(','))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    filename, mime = inspect_upload(file.filename, data)
    if project_code is not None and (len(project_code) > 80 or not project_code.replace('-', '').replace('_', '').isalnum()):
        raise HTTPException(400, 'Invalid project_code')
    sha = hashlib.sha256(data).hexdigest()
    duplicate = db.scalar(select(Document).where(Document.tenant_id == principal.tenant_id, Document.sha256 == sha))
    if duplicate:
        raise HTTPException(409, detail={'message': 'Document already uploaded', 'document_id': duplicate.id})
    stored_name = generate_reference(filename)
    try:
        store_bytes(data, stored_name, principal.tenant_id, mime)
        doc = Document(
            tenant_id=principal.tenant_id, original_filename=filename,
            stored_name=stored_name, sha256=sha, media_type=mime,
            project_code=project_code, status='queued',
        )
        db.add(doc)
        db.flush()
        db.add_all([
            DocumentGrant(tenant_id=principal.tenant_id, document_id=doc.id, role=role)
            for role in roles
        ])
        db.commit()
        db.refresh(doc)
        return {**serialize(doc), 'allowed_roles': roles}
    except IntegrityError as exc:
        db.rollback()
        best_effort_delete(stored_name, principal.tenant_id)
        raise HTTPException(409, 'Duplicate document') from exc
    except Exception:
        db.rollback()
        best_effort_delete(stored_name, principal.tenant_id)
        raise


@router.get('')
def list_documents(
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_demo_principal),
):
    docs = db.scalars(
        select(Document)
        .where(authorized_document_filter(principal))
        .order_by(Document.created_at.desc()).limit(100)
    ).all()
    return [serialize(doc) for doc in docs]


@router.get('/{document_id}')
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_demo_principal),
):
    doc = db.scalar(select(Document).where(
        Document.id == document_id, authorized_document_filter(principal)
    ))
    if doc is None:
        raise HTTPException(404, 'Document not found')
    return serialize(doc)


class PermissionChange(BaseModel):
    allowed_roles: list[str] = Field(min_length=1, max_length=3)


@router.put('/{document_id}/permissions')
def set_document_permissions(
    document_id: str,
    request: PermissionChange,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_demo_admin),
):
    try:
        roles = validate_roles(request.allowed_roles)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    doc = db.scalar(select(Document).where(
        Document.id == document_id, Document.tenant_id == principal.tenant_id
    ).with_for_update())
    if doc is None:
        raise HTTPException(404, 'Document not found')
    db.execute(delete(DocumentGrant).where(
        DocumentGrant.document_id == doc.id,
        DocumentGrant.tenant_id == principal.tenant_id,
    ))
    db.add_all([
        DocumentGrant(tenant_id=principal.tenant_id, document_id=doc.id, role=role)
        for role in roles
    ])
    db.commit()
    return {'document_id': doc.id, 'allowed_roles': roles}
