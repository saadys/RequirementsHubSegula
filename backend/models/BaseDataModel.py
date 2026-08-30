"""
models/BaseDataModel.py
Async SQLAlchemy session factory and base class for all model files.
Inspired by mini-rag-app pattern: each XModel inherits from BaseDataModel,
receives an injected AsyncSession, and performs its own DB operations.

Usage in FastAPI routes:
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSessionLocal() as session:
            yield session

    @router.post("/submissions/")
    async def create(data: ..., db: AsyncSession = Depends(get_db)):
        model = SubmissionModel(db_client=db)
        return await model.create_submission(data)
"""

import logging
import uuid
from typing import Any
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from backend.config import (
    DATABASE_URL,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_POOL_RECYCLE,
)

logger = logging.getLogger("backend.models")


def to_uuid(val: str | uuid.UUID | Any) -> uuid.UUID | None:
    """
    Safely convert a string or UUID object into a uuid.UUID instance.
    Returns None if invalid or None.
    """
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, TypeError, AttributeError):
        return None


# ── Engine (singleton) ───────────────────────────────────────────────────────
# pool_pre_ping=True: validates connection before use (handles DB restarts)
# pool_recycle: re-establishes stale connections before DB drops them (e.g. Cloud SQL limits)
# pool_size & max_overflow: managed via ENV variables to handle Cloud Run auto-scaling
connect_args = {}
if any(k in DATABASE_URL for k in ("pooler.supabase.com", "neon.tech", "ssl=require", "sslmode=require")):
    connect_args["statement_cache_size"] = 0
    connect_args["prepared_statement_cache_size"] = 0
    connect_args["ssl"] = "require"

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    connect_args=connect_args,
)

# ── Session factory ──────────────────────────────────────────────────────────
# expire_on_commit=False: prevents "DetachedInstanceError" when accessing
# attributes after commit in async context
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── FastAPI dependency ───────────────────────────────────────────────────────
async def get_db():
    """
    FastAPI dependency that yields an AsyncSession per request.
    Session is automatically closed after the request completes.
    Use with: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# ── Base Model Class ─────────────────────────────────────────────────────────
class BaseDataModel:
    """
    Base class for all model files (SubmissionModel, DepartmentModel, etc.).
    Receives an injected AsyncSession and exposes common async CRUD primitives.

    Design choice: Session injection (not class-level session) ensures
    that each request gets its own isolated transaction, preventing
    cross-request data contamination in async environments.
    """

    def __init__(self, db_client: AsyncSession):
        self.db_client = db_client

    async def save(self, instance, auto_commit: bool = True) -> None:
        """Add and commit (or flush) a single ORM instance."""
        self.db_client.add(instance)
        if auto_commit:
            await self.db_client.commit()
            await self.db_client.refresh(instance)
        else:
            await self.db_client.flush()

    async def save_and_return(self, instance, auto_commit: bool = True):
        """Add, commit (or flush), and return the refreshed ORM instance."""
        self.db_client.add(instance)
        if auto_commit:
            await self.db_client.commit()
            await self.db_client.refresh(instance)
        else:
            await self.db_client.flush()
        return instance

    async def delete(self, instance, auto_commit: bool = True) -> None:
        """Delete an ORM instance and commit (or flush)."""
        await self.db_client.delete(instance)
        if auto_commit:
            await self.db_client.commit()
        else:
            await self.db_client.flush()

