import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# backend/app/config.py lives at <root>/backend/app/config.py
# Go up: backend/app -> backend -> project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

def _get_secret_key():
    """Returns environment SECRET_KEY, or dynamically creates and caches a secure persistent key."""
    env_secret = os.getenv("SECRET_KEY", "").strip()
    if env_secret and env_secret != "dev-insecure-key-replace-in-production":
        return env_secret
    
    # If in development, return development fallback
    if os.getenv("FLASK_ENV", "development") == "development" and not os.getenv("RENDER"):
        return env_secret or "dev-insecure-key-replace-in-production"
    
    # For production without an explicit SECRET_KEY, generate and persist a secure 256-bit token
    secret_file = BASE_DIR / "backend" / "instance" / "secret_key"
    try:
        if secret_file.exists():
            return secret_file.read_text(encoding="utf-8").strip()
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        new_key = secrets.token_hex(32)
        secret_file.write_text(new_key, encoding="utf-8")
        return new_key
    except Exception:
        return secrets.token_hex(32)

def _get_database_uri():
    """Resolves database URI supporting local persistent SQLite, persistent disk mounts, and production PostgreSQL/MySQL."""
    raw_url = os.getenv("DATABASE_URL", "").strip()
    persistent_storage = os.getenv("PERSISTENT_STORAGE_PATH", "").strip()

    if not raw_url or raw_url == "sqlite:///student_mart.db":
        if persistent_storage:
            p_folder = Path(persistent_storage)
            p_folder.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{p_folder / 'student_mart.db'}"
        # Resolve to persistent path inside backend/instance folder
        instance_folder = BASE_DIR / "backend" / "instance"
        instance_folder.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{instance_folder / 'student_mart.db'}"
    
    # Normalize legacy postgres:// prefix from cloud providers to modern postgresql://
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)
    return raw_url

class Config:
    """Base application configuration."""
    SECRET_KEY = _get_secret_key()
    
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300
    } if "sqlite" not in SQLALCHEMY_DATABASE_URI else {}
    
    # Upload configuration supporting persistent disk mounts
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5 MB
    _custom_upload = os.getenv("UPLOAD_FOLDER", "").strip()
    _persistent_storage = os.getenv("PERSISTENT_STORAGE_PATH", "").strip()
    if _custom_upload:
        UPLOAD_FOLDER = Path(_custom_upload)
    elif _persistent_storage:
        UPLOAD_FOLDER = Path(_persistent_storage) / "uploads"
    else:
        UPLOAD_FOLDER = BASE_DIR / "frontend" / "static" / "uploads"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    
    # Cookie & Session Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in ("true", "1")
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days
    
    # Optional Third-Party Services
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "").strip()
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
    RAZORPAY_CURRENCY = os.getenv("RAZORPAY_CURRENCY", "INR")
    
    # Marketplace Meta
    MARKETPLACE_NAME = os.getenv("MARKETPLACE_NAME", "Student Mart")
    SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@studentmart.campus")
    DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Bengaluru, India")


class DevelopmentConfig(Config):
    """Configuration for local development."""
    DEBUG = True
    ENV = "development"


class TestingConfig(Config):
    """Configuration for unit and integration testing."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret-key-12345"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Configuration for production deployment."""
    DEBUG = False
    ENV = "production"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() in ("true", "1")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
