"""Local-only Task 3 configuration. Add real auth before network deployment."""
import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / '.env')
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql+psycopg://eki:local_only_password@localhost:5433/eki')
DEV_API_KEY = os.environ.get('DEV_API_KEY', '')
APP_MODE = os.environ.get('APP_MODE', 'local')
STORAGE_DIR = BACKEND_DIR / 'data' / 'uploads'
EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
EMBEDDING_DIMS = 384
DEV_TENANT_ID = '00000000-0000-0000-0000-000000000001'
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
