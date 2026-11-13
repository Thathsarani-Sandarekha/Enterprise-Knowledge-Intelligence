# Optional Amazon S3 storage setup

## Design and safety

- Local storage remains default (`STORAGE_BACKEND=local`).
- Switching to `s3` affects *new* documents only. Existing UUID-based local references remain local; S3 references have a `s3:` prefix stored in the existing `documents.stored_name` column. No DB migration required.
- Object keys are prefixed by tenant ID: `S3_KEY_PREFIX/<tenant-id>/<uuid.ext>`. Keys and the bucket are never exposed as public URLs.
- Only the FastAPI/worker uses S3; access control still happens in FastAPI/PostgreSQL. S3 is private and must have Block Public Access enabled.
- Docling processes a temporary local copy of S3 files. The copy is cleaned up after extraction.
- Do not use real confidential customer documents for your public demo.

## Configure

1. Create a **private** S3 bucket in an AWS region you control. Enable Block Public Access and default bucket encryption.
2. Grant the backend identity only `s3:PutObject`, `s3:GetObject`, and `s3:DeleteObject` to your dedicated object prefix. Use IAM roles or the normal AWS CLI profile; never commit access keys. A limited CLI profile is suitable for local testing.
3. In `docmind_env`, from `backend`: `python -m pip install -r requirements-s3.txt`.
4. Add these values to **untracked** `backend/.env` (use `.env.s3.example` as a reference):

```dotenv
STORAGE_BACKEND=s3
AWS_S3_BUCKET=your-private-bucket
AWS_REGION=us-east-1
S3_KEY_PREFIX=hospitality-documents
```

5. If authenticating with a local AWS CLI profile, set `AWS_PROFILE` in your shell, or otherwise provide role-based credentials using the boto3 credential chain.
6. Run credential-free tests: `python -m pytest -q tests/test_s3_storage_adapter.py`.
7. Run live smoke (uses and deletes one small object): `python -m scripts.s3_storage_smoke`.
8. Restart API **and** ingestion worker. Upload one synthetic PDF and confirm `status=ready` in the UI. This final step is needed to claim end-to-end S3 ingestion as working.
9. To return to local storage for future uploads, set `STORAGE_BACKEND=local` and restart the processes.

## Example object-prefix IAM permission policy

Replace the bucket and prefix with your own values. Restrict credentials to the trusted application service; no public ACLs or browser direct-access URLs are used.

```json
{
  "Version":"2012-10-17",
  "Statement":[{"Effect":"Allow","Action":["s3:PutObject","s3:GetObject","s3:DeleteObject"],"Resource":"arn:aws:s3:::YOUR-BUCKET/hospitality-documents/*"}]
}
```

Bucket encryption, network policy, tenant-specific IAM isolation and audit logs are operational requirements beyond this adapter; the IAM above is application-prefix-scoped, not a separate IAM role per tenant.

### Docker note

The container needs `boto3` installed plus an authorized credential source *inside the container*. The release installer adds the optional dependency to `requirements-demo.txt` when found. Do not copy `~/.aws/credentials` or private keys into Docker images or Git. Use local mode when cloud credentials are unavailable. AWS compute deployment is explicitly a **future architecture concept**, not the result of adding S3 storage support.

## Official API references

- https://docs.aws.amazon.com/boto3/latest/guide/s3-uploading-files.html
- https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/download_fileobj.html
