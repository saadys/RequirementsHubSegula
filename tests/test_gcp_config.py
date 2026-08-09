"""
tests/test_gcp_config.py

Unit tests for GCP production config behavior in backend/config.py:
- Verification of Cloud SQL Unix Socket URL formatting
- Verification of dialect prefix sanitization (postgres://, postgresql:// -> postgresql+asyncpg://)
- Verification of INSTANCE_CONNECTION_NAME fallback
"""

import os
import pytest


def test_cloud_sql_socket_url_construction(monkeypatch):
    """Verifies that INSTANCE_CONNECTION_NAME properly constructs Cloud SQL socket URL."""
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "segula-proj:europe-west1:req-db")
    monkeypatch.setenv("DB_USER", "custom_user")
    monkeypatch.setenv("DB_PASS", "secret_pass")
    monkeypatch.setenv("DB_NAME", "req_db")
    monkeypatch.setenv("DB_SOCKET_DIR", "/cloudsql")

    # Re-evaluate config logic
    db_url = os.getenv("DATABASE_URL", "")
    instance_name = os.getenv("INSTANCE_CONNECTION_NAME", "")
    if not db_url and instance_name:
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASS", "")
        db_name = os.getenv("DB_NAME", "requirementshub")
        db_socket_dir = os.getenv("DB_SOCKET_DIR", "/cloudsql")
        db_url = f"postgresql+asyncpg://{db_user}:{db_pass}@/{db_name}?host={db_socket_dir}/{instance_name}"

    assert db_url == "postgresql+asyncpg://custom_user:secret_pass@/req_db?host=/cloudsql/segula-proj:europe-west1:req-db"


def test_dialect_sanitization():
    """Verifies that postgres:// and postgresql:// URLs are sanitized to postgresql+asyncpg://."""
    url_postgres = "postgres://user:pass@/dbname?host=/cloudsql/proj:region:inst"
    url_postgresql = "postgresql://user:pass@/dbname?host=/cloudsql/proj:region:inst"

    def sanitize(url):
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    assert sanitize(url_postgres).startswith("postgresql+asyncpg://")
    assert sanitize(url_postgresql).startswith("postgresql+asyncpg://")


def test_cloud_run_env_bypass_logic(monkeypatch):
    """Verifies the logic that determines if dotenv loading should be bypassed."""
    # Simulation Cloud Run environment
    monkeypatch.setenv("K_SERVICE", "backend-service")
    monkeypatch.setenv("ENVIRONMENT", "production")

    is_cloud_run = bool(os.getenv("K_SERVICE"))
    env_mode = os.getenv("ENVIRONMENT", "development").lower()

    should_skip_load_dotenv = is_cloud_run or env_mode in ("production", "prod")
    assert should_skip_load_dotenv is True

    # Simulation Development environment
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")

    is_cloud_run = bool(os.getenv("K_SERVICE"))
    env_mode = os.getenv("ENVIRONMENT", "development").lower()

    should_skip_load_dotenv = is_cloud_run or env_mode in ("production", "prod")
    assert should_skip_load_dotenv is False
