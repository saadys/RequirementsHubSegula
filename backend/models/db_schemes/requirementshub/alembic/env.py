"""
models/db_schemes/requirementshub/alembic/env.py
Alembic environment config for async SQLAlchemy (asyncpg driver).
Co-located with the DB definition — style mini-rag-app.

Key decisions:
- run_async_migrations(): uses AsyncEngine to not block event loop
- target_metadata = Base.metadata: enables --autogenerate detection
- DATABASE_URL read from backend.config (single source of truth)
"""

import asyncio
import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

# Import Base + all models so Alembic can detect them in metadata
from backend.models.db_schemes.requirementshub.schemes import (  # noqa: F401
    Base,
    Department,
    Submission,
    FactExtraction,
    ScoringResult,
    ClarificationRound,
    Report,
    ReviewerOverride,
    HistoricProject,
)
from backend.config import DATABASE_URL

logger = logging.getLogger("alembic.env")

# Alembic Config object (reads alembic.ini)
config = context.config

# Setup Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with our config (avoids hardcoding in alembic.ini)
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# This is used by --autogenerate to detect schema differences
target_metadata = Base.metadata


# Indexes created with raw SQL (pgvector HNSW) cannot be expressed on the ORM
# model, so autogenerate sees them as "in the database but not in metadata" and
# proposes to drop them. Excluding them keeps `alembic check` meaningful:
# a real drift is reported, this known-managed-elsewhere object is not.
RAW_SQL_MANAGED_INDEXES = frozenset({"idx_historic_projects_embedding_hnsw"})


def include_object(object_, name, type_, reflected, compare_to):
    """Filter objects that autogenerate must ignore."""
    if type_ == "index" and name in RAW_SQL_MANAGED_INDEXES:
        return False
    return True


def run_migrations_offline() -> None:
    """
    Offline mode: generate SQL script without connecting to DB.
    Useful for review before applying migrations.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Online mode: connects to the DB using async engine (asyncpg).
    Required because SQLAlchemy async engine cannot run in sync context.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # NullPool for migration: no pooling needed
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
