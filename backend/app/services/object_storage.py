"""Optional document object storage. Existing local references remain readable.

A reference starts with `s3:` only if its original bytes were stored in S3.
The document tenant is always supplied from the trusted DB/principal, never from
an external object-store key or the user-provided filename.
"""
from __future__ import annotations

import logging
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from app.config import STORAGE_DIR

logger = logging.getLogger(__name__)
_REF = re.compile(r'^[0-9a-f]{32}\.(pdf|docx|xlsx)$')
_LEGACY_REF = re.compile(r'^[0-9a-fA-F-]{36}\.(pdf|docx|xlsx)$')
_TENANT = re.compile(r'^[a-zA-Z0-9_-]{1,80}$')


def _settings() -> tuple[str, str, str]:
    mode = os.environ.get('STORAGE_BACKEND', 'local').strip().lower()
    if mode not in {'local', 's3'}:
        raise ValueError('STORAGE_BACKEND must be local or s3')
    bucket = os.environ.get('AWS_S3_BUCKET', '').strip()
    prefix = os.environ.get('S3_KEY_PREFIX', 'hospitality-documents').strip('/')
    if not re.fullmatch(r'[A-Za-z0-9/_-]{1,120}', prefix) or '..' in prefix:
        raise ValueError('Invalid S3_KEY_PREFIX')
    if mode == 's3' and not bucket:
        raise ValueError('AWS_S3_BUCKET is required with STORAGE_BACKEND=s3')
    return mode, bucket, prefix


def _check_ref(ref: str) -> str:
    value = ref[3:] if ref.startswith('s3:') else ref
    if not (_REF.fullmatch(value) or _LEGACY_REF.fullmatch(value)):
        raise ValueError('Invalid stored object reference')
    return value


def _s3_key(ref: str, tenant_id: str) -> str:
    value = _check_ref(ref)
    if not _TENANT.fullmatch(tenant_id):
        raise ValueError('Invalid tenant identifier')
    _, _, prefix = _settings()
    return f'{prefix}/{tenant_id}/{value}'


def get_s3_client():
    """Boto3 uses its standard credential chain; never hardcode credentials."""
    import boto3
    region = os.environ.get('AWS_REGION') or None
    return boto3.client('s3', region_name=region)


def generate_reference(original_filename: str) -> str:
    suffix = Path(original_filename).suffix.lower()
    if suffix not in {'.pdf', '.docx', '.xlsx'}:
        raise ValueError('Unsupported file extension')
    mode, _, _ = _settings()
    ref = f'{uuid4().hex}{suffix}'
    return f's3:{ref}' if mode == 's3' else ref


def store_bytes(data: bytes, ref: str, tenant_id: str, media_type: str) -> None:
    """Store already validated upload bytes. Never exposes a public S3 URL."""
    value = _check_ref(ref)
    if ref.startswith('s3:'):
        from io import BytesIO
        _, bucket, _ = _settings()
        if not bucket:
            raise ValueError('AWS_S3_BUCKET required to store S3 object')
        get_s3_client().upload_fileobj(
            BytesIO(data), bucket, _s3_key(ref, tenant_id),
            ExtraArgs={'ContentType': media_type},
        )
        return
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    with (STORAGE_DIR / value).open('xb') as handle:
        handle.write(data)


@contextmanager
def materialized_document(ref: str, tenant_id: str):
    """Yield a local Path for Docling/extraction; wipe S3 temp file afterward."""
    value = _check_ref(ref)
    if not ref.startswith('s3:'):
        yield STORAGE_DIR / value
        return
    _, bucket, _ = _settings()
    if not bucket:
        raise ValueError('AWS_S3_BUCKET required to retrieve S3 object')
    with tempfile.TemporaryDirectory(prefix='eki_parse_') as folder:
        local_path = Path(folder) / value
        with local_path.open('wb') as handle:
            get_s3_client().download_fileobj(bucket, _s3_key(ref, tenant_id), handle)
        yield local_path


def delete_object(ref: str, tenant_id: str) -> None:
    value = _check_ref(ref)
    if ref.startswith('s3:'):
        _, bucket, _ = _settings()
        if not bucket:
            raise ValueError('AWS_S3_BUCKET required to delete S3 object')
        get_s3_client().delete_object(Bucket=bucket, Key=_s3_key(ref, tenant_id))
    else:
        (STORAGE_DIR / value).unlink(missing_ok=True)


def best_effort_delete(ref: str, tenant_id: str) -> None:
    try:
        delete_object(ref, tenant_id)
    except Exception as exc:
        # Do not mask the original DB transaction failure or leak file contents.
        logger.error('Storage cleanup failed: error_type=%s', type(exc).__name__)
