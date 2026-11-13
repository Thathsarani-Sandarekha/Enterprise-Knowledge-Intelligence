"""Real opt-in S3 upload/download/delete smoke; does not touch the database.

Run only after configuring an authorized private S3 bucket and IAM credentials.
Creates and removes one tiny synthetic text object under a smoke-test prefix.
"""
from datetime import datetime, timezone
import os
from uuid import uuid4
from io import BytesIO
from app.services.object_storage import get_s3_client


def main():
    bucket = os.getenv('AWS_S3_BUCKET', '').strip()
    prefix = os.getenv('S3_KEY_PREFIX', 'hospitality-documents').strip('/')
    if not bucket:
        raise SystemExit('Set AWS_S3_BUCKET before running the S3 smoke test')
    key = f'{prefix}/smoke-test/{uuid4().hex}.txt'
    data = b'Synthetic Asteria S3 integration smoke test.\n'
    client = get_s3_client()
    try:
        client.upload_fileobj(BytesIO(data), bucket, key)
        output = BytesIO()
        client.download_fileobj(bucket, key, output)
        assert output.getvalue() == data, 'Downloaded bytes do not match uploaded bytes'
        print('PASS: real S3 upload/download round-trip (test object only)')
    finally:
        client.delete_object(Bucket=bucket, Key=key)
        print('S3 smoke test object cleanup attempted')


if __name__ == '__main__':
    main()
