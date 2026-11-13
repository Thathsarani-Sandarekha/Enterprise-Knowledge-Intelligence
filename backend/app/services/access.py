"""Single source of truth for SQL-side document authorization.

Always combine role checks with tenant constraints. Never retrieve broad data
and filter it in Python AFTER it has been sent to an external LLM.
"""
from sqlalchemy import and_, exists, or_
from app.models import Document, DocumentGrant
from app.routes.principals import Principal


def authorized_document_filter(principal: Principal):
    tenant_match = Document.tenant_id == principal.tenant_id
    if principal.role == 'admin':
        return tenant_match
    return and_(
        tenant_match,
        exists().where(
            DocumentGrant.document_id == Document.id,
            DocumentGrant.tenant_id == principal.tenant_id,
            DocumentGrant.role == principal.role,
        ),
    )


def validate_roles(roles: list[str]) -> list[str]:
    from app.routes.principals import ROLES
    normalized = list(dict.fromkeys(role.strip().lower() for role in roles))
    if not normalized or any(role not in ROLES for role in normalized):
        raise ValueError('Roles must be a non-empty subset of designer, procurement, project_manager')
    return normalized
