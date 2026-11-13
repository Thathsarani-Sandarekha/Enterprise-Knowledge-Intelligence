# Asteria Studio — Windows release gate

The S3 patch must first be installed using `python apply_release_kit.py` from the **project root**.

## 1. Validate source and tests (Conda)

```cmd
cd /d F:\Github\enterprise-knowledge-intelligence\backend
python -m pip install -r requirements.txt
python -m py_compile app\routes\documents.py app\services\ingestion.py app\services\object_storage.py
python -m pytest -q
cd ..\frontend
npm run typecheck
npm run build
```

## 2. Verify Compose

```cmd
cd /d F:\Github\enterprise-knowledge-intelligence
docker compose -f docker-compose.yml -f compose.demo.yml config --quiet
docker compose -f docker-compose.yml -f compose.demo.yml up --build -d
docker compose -f docker-compose.yml -f compose.demo.yml ps
docker compose -f docker-compose.yml -f compose.demo.yml logs --tail=80 api frontend worker
```

Build problems caused by Docker Hub network timeouts are not proof of application failure. Keep them as an explicit release limitation until verified.

## 3. Verify local or cloud document flow

Local mode remains default. For actual cloud verification, configure a private S3 bucket and least-privilege credentials as described in `S3_SETUP.md`, then:

```cmd
cd /d F:\Github\enterprise-knowledge-intelligence\backend
python -m scripts.s3_storage_smoke
```

S3 object roundtrip is not a substitute for a full frontend upload -> queue -> ready -> RAG query test.

## 4. Audit Git before public push

```cmd
cd /d F:\Github\enterprise-knowledge-intelligence
git status --short
git add .
git diff --cached --name-only
git diff --cached --check
```

Review staged content manually for secrets, user uploads, real client names, tokens, private datasets, and accidentally tracked files. Do not commit until reviewed. After creating your GitHub repo:

```cmd
git branch -M main
git commit -m "Release Asteria Studio portfolio demo"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

GitHub Actions will show whether tests and image builds pass on actual hosted runners; a committed workflow is not itself a passing CI run.

## 5. Video and result claims

Follow `DEMO_SCRIPT.md`. Use real application screenshots. Present the 3-document retrieval pilot, observed access tests, and the original 10/15 answer checks with disclosed limitations; do not present them as full production guarantees.
