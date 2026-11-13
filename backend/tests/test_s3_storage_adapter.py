"""Credential-free storage tests: local compatibility and mocked S3 path."""
from io import BytesIO
from pathlib import Path

import pytest
from app.services import object_storage as store


class FakeS3:
    def __init__(self):
        self.objects = {}

    def upload_fileobj(self, fp, bucket, key, ExtraArgs=None):
        self.objects[(bucket, key)] = fp.read()

    def download_fileobj(self, bucket, key, fp):
        fp.write(self.objects[(bucket, key)])

    def delete_object(self, Bucket, Key):
        self.objects.pop((Bucket, Key), None)


def test_local_round_trip_and_path_safety(tmp_path, monkeypatch):
    monkeypatch.setenv('STORAGE_BACKEND', 'local')
    monkeypatch.setattr(store, 'STORAGE_DIR', tmp_path)
    ref = store.generate_reference('finish_approval.pdf')
    assert not ref.startswith('s3:')
    store.store_bytes(b'test-pdf', ref, 'tenant-one', 'application/pdf')
    with store.materialized_document(ref, 'tenant-one') as path:
        assert path.read_bytes() == b'test-pdf'
    store.delete_object(ref, 'tenant-one')
    assert not (tmp_path / ref).exists()
    with pytest.raises(ValueError):
        store.store_bytes(b'secret', '../bad.pdf', 'tenant-one', 'application/pdf')


def test_s3_upload_download_cleanup_and_tenant_keys(monkeypatch):
    fake = FakeS3()
    monkeypatch.setenv('STORAGE_BACKEND', 's3')
    monkeypatch.setenv('AWS_S3_BUCKET', 'dummy-private-bucket')
    monkeypatch.setenv('S3_KEY_PREFIX', 'eki-demo')
    monkeypatch.setattr(store, 'get_s3_client', lambda: fake)
    ref = store.generate_reference('quote.xlsx')
    assert ref.startswith('s3:')
    store.store_bytes(b'fake-xlsx', ref, 'tenant-a', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    key = store._s3_key(ref, 'tenant-a')
    assert key.startswith('eki-demo/tenant-a/')
    with store.materialized_document(ref, 'tenant-a') as path:
        assert path.read_bytes() == b'fake-xlsx'
        materialized_path = Path(path)
    assert not materialized_path.exists()
    store.delete_object(ref, 'tenant-a')
    assert fake.objects == {}


def test_existing_local_reference_stays_local_if_s3_enabled(tmp_path, monkeypatch):
    monkeypatch.setenv('STORAGE_BACKEND', 's3')
    monkeypatch.setenv('AWS_S3_BUCKET', 'dummy-private-bucket')
    monkeypatch.setattr(store, 'STORAGE_DIR', tmp_path)
    existing = '12345678-1234-1234-1234-123456789abc.pdf'
    (tmp_path / existing).write_bytes(b'original-local-file')
    with store.materialized_document(existing, 'tenant-a') as p:
        assert p.read_bytes() == b'original-local-file'


def test_invalid_backend_or_bucket_is_explicit(monkeypatch):
    monkeypatch.setenv('STORAGE_BACKEND', 'invalid')
    with pytest.raises(ValueError):
        store.generate_reference('hotel.docx')
    monkeypatch.setenv('STORAGE_BACKEND', 's3')
    monkeypatch.delenv('AWS_S3_BUCKET', raising=False)
    with pytest.raises(ValueError):
        store.generate_reference('hotel.docx')
