import os
import shutil
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Base package directory (src/moodle_bot)
PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent

# Load environment variables from .env
env_file = PROJECT_ROOT / ".env"
if env_file.exists() and load_dotenv:
    load_dotenv(env_file)

# Central runtime data directory (stored at project root, outside src/)
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Database paths
DB_PATH = DATA_DIR / "lms_app.db"
SESSION_DB_PATH = DATA_DIR / "session.sqlite3"

# Seamlessly preserve any existing local data from legacy path
_legacy_cache = PACKAGE_DIR / "data" / "cache"
if _legacy_cache.exists():
    _legacy_db = _legacy_cache / "lms_app.db"
    if _legacy_db.exists() and not DB_PATH.exists():
        shutil.copy2(_legacy_db, DB_PATH)

    _legacy_session = _legacy_cache / "session.sqlite3"
    if _legacy_session.exists() and not SESSION_DB_PATH.exists():
        shutil.copy2(_legacy_session, SESSION_DB_PATH)

    for _item in _legacy_cache.glob("*.json"):
        _target = CACHE_DIR / _item.name
        if not _target.exists():
            shutil.copy2(_item, _target)

# Environment settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEFAULT_PHONE_NUMBER = os.getenv("DEFAULT_PHONE_NUMBER", "")
