"""Explicitly temporary local demo access gate; NOT enterprise authentication."""
import secrets
from fastapi import Header, HTTPException
from app.config import APP_MODE, DEV_API_KEY


def require_local_key(x_api_key: str | None = Header(default=None)) -> None:
    if APP_MODE != 'local' or not DEV_API_KEY:
        raise HTTPException(503, 'Real authentication is not configured; local API disabled')
    if x_api_key is None or not secrets.compare_digest(x_api_key, DEV_API_KEY):
        raise HTTPException(401, 'Invalid development API key')
