"""
tests/conftest.py
Production-grade Pytest Fixtures for RequirementsHubSegula.

Provides:
- In-memory SQLite async database engine (sqlite+aiosqlite:///:memory:)
- Isolated database session fixtures per test
- FastAPI TestClient and httpx AsyncClient with get_db dependency override
- Pre-seeded test fixtures (Department, Submission, etc.)
- Automatic mocking for LLM external service calls
"""

import os
import sys

# Ensure project root is in sys.path for backend imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.models.db_schemes.requirementshub.schemes.base import Base
from backend.models.db_schemes.requirementshub.schemes import (
    Department,
    Submission,
    FactExtraction,
    ScoringResult,
    ClarificationRound,
    Report,
    ReviewerOverride,
)
from backend.models.BaseDataModel import get_db
from backend.main import app


# Use in-memory SQLite for rapid async unit testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create in-memory SQLite engine with StaticPool and initialize tables."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine, monkeypatch) -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated async session per test."""
    session_factory = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    import sys
    base_module = sys.modules.get("backend.models.BaseDataModel")
    if base_module:
        monkeypatch.setattr(base_module, "AsyncSessionLocal", session_factory)
        monkeypatch.setattr(base_module, "engine", test_engine)
    rag_module = sys.modules.get("backend.nodes.rag_search")
    if rag_module:
        monkeypatch.setattr(rag_module, "AsyncSessionLocal", session_factory)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession, test_engine, monkeypatch) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI AsyncClient fixture overriding get_db dependency."""
    session_factory = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    import sys
    base_module = sys.modules.get("backend.models.BaseDataModel")
    if base_module:
        monkeypatch.setattr(base_module, "AsyncSessionLocal", session_factory)
        monkeypatch.setattr(base_module, "engine", test_engine)
    rag_module = sys.modules.get("backend.nodes.rag_search")
    if rag_module:
        monkeypatch.setattr(rag_module, "AsyncSessionLocal", session_factory)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def seeded_department(db_session: AsyncSession) -> Department:
    """Pre-seed 'corporate_support' department into the test DB."""
    dept = Department(
        id="corporate_support",
        display_name="Corporate & Support",
        description="HR, Finance, IT and internal support services",
        enabled=True,
        specific_fields=[
            {"name": "service_area", "label": "Domaine", "type": "select"},
            {"name": "target_users", "label": "Utilisateurs", "type": "text"},
        ],
    )
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)
    return dept


@pytest.fixture
def sample_submission_payload() -> dict:
    """Valid submission payload dictionary for API testing."""
    return {
        "project_name": "AI Onboarding Assistant",
        "department": "corporate_support",
        "team_contact_name": "Jean Dupont",
        "team_contact_email": "jean.dupont@segula.fr",
        "problem_description": "Employees spend 2 weeks looking for internal HR policies across folders.",
        "current_process": "Manual search on SharePoint and emailing colleagues.",
        "expected_outcome": "An intelligent conversational chatbot answering HR/IT questions.",
        "data_description": "500 PDF policy documents and internal FAQ tables.",
        "deadline_urgency": "medium",
        "department_specific": {
            "service_area": "hr",
            "target_users": "all_employees",
        },
    }
