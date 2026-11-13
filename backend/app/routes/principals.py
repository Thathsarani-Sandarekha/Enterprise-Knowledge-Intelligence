"""LOCAL DEMO ONLY: fixed fictional employees behind the shared development key.

x-demo-user is NOT authenticated identity. Anyone with DEV_API_KEY can choose it.
Do not deploy these routes with real/private documents or expose the server.
Replace with a verified JWT/session and DB-backed memberships before deployment.
"""
from dataclasses import dataclass
from fastapi import Depends, Header, HTTPException
from app.config import APP_MODE, DEV_TENANT_ID
from app.routes.security import require_local_key

RIVAL_TENANT_ID = '00000000-0000-0000-0000-000000000002'
ROLES = frozenset({'designer', 'procurement', 'project_manager'})


@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    role: str


DEMO_USERS = {
    'aster-admin': Principal('aster-admin', DEV_TENANT_ID, 'admin'),
    'aster-designer': Principal('aster-designer', DEV_TENANT_ID, 'designer'),
    'aster-procurement': Principal('aster-procurement', DEV_TENANT_ID, 'procurement'),
    'aster-pm': Principal('aster-pm', DEV_TENANT_ID, 'project_manager'),
    'rival-admin': Principal('rival-admin', RIVAL_TENANT_ID, 'admin'),
    'rival-designer': Principal('rival-designer', RIVAL_TENANT_ID, 'designer'),
}


def get_demo_principal(
    x_demo_user: str | None = Header(default=None, alias='x-demo-user'),
    _key: None = Depends(require_local_key),
) -> Principal:
    if APP_MODE != 'local':
        raise HTTPException(503, 'Real user authentication not yet configured')
    if x_demo_user is None or x_demo_user not in DEMO_USERS:
        raise HTTPException(401, 'Unknown or missing local demo identity')
    return DEMO_USERS[x_demo_user]


def require_demo_admin(principal: Principal = Depends(get_demo_principal)) -> Principal:
    if principal.role != 'admin':
        raise HTTPException(403, 'Administrator role required')
    return principal
