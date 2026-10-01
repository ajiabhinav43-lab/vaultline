import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # --- Database ---
    # Local dev defaults to SQLite. In production, DATABASE_URL points at
    # your Supabase PostgreSQL connection string (Settings > Database >
    # Connection string > URI, in Supabase). Example:
    #   postgresql://postgres.xxxxx:PASSWORD@aws-0-region.pooler.supabase.com:6543/postgres
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'app.db')}"
    )
    # Supabase's pooler drops idle connections; recycle before that happens.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- File storage ---
    # STORAGE_BACKEND is auto-detected in create_app: 'supabase' if
    # SUPABASE_URL + SUPABASE_KEY are set, otherwise 'local'.
    STORAGE_ROOT = os.environ.get("STORAGE_ROOT", os.path.join(basedir, "storage"))
    QUARANTINE_ROOT = os.path.join(STORAGE_ROOT, "quarantine")

    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "vaultline-documents")

    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB
    ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "pptx", "jpg", "jpeg", "png", "txt"}

    # --- Sessions / cookies ---
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"

    # --- CSRF ---
    WTF_CSRF_ENABLED = True

    # --- Login security ---
    MAX_FAILED_LOGIN_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15

    # --- Sharing ---
    SHARE_TOKEN_BYTES = 32


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
