"""Idempotent one-line Next.js gateway modification for Docker Compose demo.

Only allows the exact Compose-internal backend URL when DOCKER_LOCAL_DEMO=1.
Does not modify other gateway behavior. Makes a backup on first edit.
"""
from pathlib import Path
import sys
import tempfile
import hashlib

root = Path(__file__).resolve().parents[1]
file = root / 'frontend' / 'app' / 'api' / 'gateway' / '[...path]' / 'route.ts'
if not file.is_file():
    sys.exit('Cannot find Next.js gateway route. No changes made.')
content = file.read_text(encoding='utf-8')
old = r"""  if (!/^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?\/?$/.test(base)) {"""
# The raw string above must match the JS regexp in Task 5 exactly.
new = r"""  const localhostBackend = /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?\/?$/.test(base);
  const composeBackend = process.env.DOCKER_LOCAL_DEMO === "1" && base === "http://api:8000";
  if (!localhostBackend && !composeBackend) {"""
if 'const composeBackend = process.env.DOCKER_LOCAL_DEMO' in content:
    print('Already patched; no changes needed.')
elif old not in content:
    sys.exit('Expected gateway validation line not found; manual review required. No changes made.')
else:
    ident = hashlib.sha256(str(file).encode('utf-8')).hexdigest()[:10]
    backup = Path(tempfile.gettempdir()) / f'eki_gateway_{ident}.ts.bak'
    if not backup.exists():
        backup.write_text(content, encoding='utf-8')
    file.write_text(content.replace(old, new, 1), encoding='utf-8')
    print('Patched Docker-local backend hostname support; backup:', backup)
