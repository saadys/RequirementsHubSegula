"""
tests/test_cli_seed.py

Unit and Integration tests for backend/cli/seed.py (Factor XII Admin Process).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI

from backend.cli.seed import run_seed
from backend.services.vectorstore import load_seed_data
from backend.models.db_schemes.requirementshub.schemes.historic_project import HistoricProject
from backend.main import startup_span


@pytest.mark.asyncio
async def test_factor_xii_web_startup_decoupled_from_seed():
    """
    Factor XII Compliance Test:
    Verifies that Web application startup (startup_span in main.py) ONLY initializes
    the DB engine pool and NEVER triggers RAG data seeding (load_seed_data).
    """
    app = FastAPI()
    with patch("backend.services.vectorstore.load_seed_data") as mock_load_seed, \
         patch("backend.services.vectorstore.is_seed_data_loaded") as mock_is_loaded:

        await startup_span(app)

        # 1. Verify Web server successfully initializes DB engine state
        assert hasattr(app.state, "db_engine")

        # 2. Verify RAG seed functions are NEVER called during Web startup
        mock_load_seed.assert_not_called()
        mock_is_loaded.assert_not_called()


@pytest.mark.asyncio
async def test_run_seed_when_empty():
    """Test run_seed triggers load_seed_data when table is empty."""
    mock_conn = AsyncMock()
    mock_engine = MagicMock()
    mock_engine.begin.return_value.__aenter__.return_value = mock_conn
    mock_engine.dispose = AsyncMock()

    mock_db = AsyncMock()
    mock_session_local = MagicMock()
    mock_session_local.return_value.__aenter__.return_value = mock_db

    with patch("backend.cli.seed.engine", mock_engine), \
         patch("backend.cli.seed.AsyncSessionLocal", mock_session_local), \
         patch("backend.cli.seed.is_seed_data_loaded", new=AsyncMock(return_value=False)) as mock_is_loaded, \
         patch("backend.cli.seed.load_seed_data", new=AsyncMock()) as mock_load:

        await run_seed()

        mock_is_loaded.assert_awaited_once_with(mock_db)
        mock_load.assert_awaited_once_with(mock_db)
        mock_engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_seed_skips_when_already_loaded():
    """Test run_seed skips load_seed_data when data is already present."""
    mock_conn = AsyncMock()
    mock_engine = MagicMock()
    mock_engine.begin.return_value.__aenter__.return_value = mock_conn
    mock_engine.dispose = AsyncMock()

    mock_db = AsyncMock()
    mock_session_local = MagicMock()
    mock_session_local.return_value.__aenter__.return_value = mock_db

    with patch("backend.cli.seed.engine", mock_engine), \
         patch("backend.cli.seed.AsyncSessionLocal", mock_session_local), \
         patch("backend.cli.seed.is_seed_data_loaded", new=AsyncMock(return_value=True)) as mock_is_loaded, \
         patch("backend.cli.seed.load_seed_data", new=AsyncMock()) as mock_load:

        await run_seed()

        mock_is_loaded.assert_awaited_once_with(mock_db)
        mock_load.assert_not_awaited()
        mock_engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_seed_handles_error_and_exits():
    """Test run_seed catches exceptions, exits with code 1, and disposes engine."""
    mock_engine = MagicMock()
    mock_engine.begin.side_effect = Exception("DB Connection Refused")
    mock_engine.dispose = AsyncMock()

    with patch("backend.cli.seed.engine", mock_engine), \
         patch("sys.exit") as mock_exit:

        await run_seed()

        mock_exit.assert_called_once_with(1)
        mock_engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_load_seed_data_integration():
    """Integration test: load_seed_data parses JSON file, generates embeddings, and saves to DB."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.get.return_value = None  # Force entry insertion

    dummy_vector = [0.05] * 768
    with patch("backend.services.vectorstore.generate_embedding", new=AsyncMock(return_value=dummy_vector)):
        await load_seed_data(mock_db)

    # Verify that records from historic_projects.json were inserted into ORM
    assert mock_db.add.call_count > 0
    first_record = mock_db.add.call_args_list[0][0][0]
    assert isinstance(first_record, HistoricProject)
    assert first_record.embedding == dummy_vector
    mock_db.commit.assert_awaited_once()
