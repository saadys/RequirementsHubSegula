"""Tests for RAG retrieval service with pgvector backend. Owner: Track A"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Unit tests: search_similar (mocked DB + embedding) ───────────────────────

@pytest.mark.asyncio
async def test_search_similar_returns_results():
    """Verifies search_similar returns correct tuple structure from mock DB."""
    from backend.services.vectorstore import search_similar

    mock_row = MagicMock()
    mock_row.id = "irfane-001"
    mock_row.project_name = "IRFANE Chatbot"
    mock_row.problem_description = "HR knowledge accessibility challenges"
    mock_row.solution_description = "AI RAG-powered assistant"
    mock_row.tags = ["chatbot", "hr"]
    mock_row.raw_json = {"id": "irfane-001", "project_name": "IRFANE Chatbot"}
    mock_row.similarity = 0.87

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    with patch("backend.services.vectorstore.generate_embedding", return_value=[0.1] * 768):
        results = await search_similar("chatbot for onboarding", top_k=2, db=mock_db)

    assert len(results) == 1
    doc, score, meta = results[0]
    assert score == pytest.approx(0.87)
    assert meta["project_name"] == "IRFANE Chatbot"
    assert "Problem:" in doc


@pytest.mark.asyncio
async def test_search_similar_empty_results():
    """Verifies search_similar handles empty DB results gracefully."""
    from backend.services.vectorstore import search_similar

    mock_result = MagicMock()
    mock_result.fetchall.return_value = []

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    with patch("backend.services.vectorstore.generate_embedding", return_value=[0.0] * 768):
        results = await search_similar("completely unrelated query", top_k=2, db=mock_db)

    assert results == []


# ── Unit tests: rag_search node (mocked vectorstore) ─────────────────────────

@pytest.mark.asyncio
async def test_rag_node_finds_similar_project():
    """Verifies rag_search node correctly maps high-score results above similarity threshold."""
    from backend.nodes.rag_search import rag_search

    mock_meta = {"id": "irfane-001", "project_name": "IRFANE Chatbot"}
    mock_db = AsyncMock()

    from backend import config
    sim_score = min(0.99, getattr(config, "RAG_SIMILAR_THRESHOLD", 0.60) + 0.01)
    exact_threshold = getattr(config, "RAG_EXACT_MATCH_THRESHOLD", 0.83)
    if sim_score >= exact_threshold:
        sim_score = exact_threshold - 0.01

    with patch(
        "backend.nodes.rag_search.search_similar",
        return_value=[("Problem: HR issues", sim_score, mock_meta)]
    ):
        state = {
            "form_data": {
                "problem_description": "chatbot for new employee onboarding and HR search"
            },
            "parsed_files_text": [],
        }
        result = await rag_search(state, db=mock_db)


    assert "similar_projects" in result
    assert len(result["similar_projects"]) == 1
    assert result["similar_projects"][0]["project_name"] == "IRFANE Chatbot"
    assert result["is_exact_match"] is False



@pytest.mark.asyncio
async def test_rag_node_detects_exact_match():
    """Verifies rag_search node flags exact matches (score >= RAG_EXACT_MATCH_THRESHOLD)."""
    from backend.nodes.rag_search import rag_search

    mock_meta = {"id": "talentium-001", "project_name": "Talentium"}
    mock_db = AsyncMock()

    with patch(
        "backend.nodes.rag_search.search_similar",
        return_value=[("Problem: CV screening", 0.96, mock_meta)]
    ):
        state = {
            "form_data": {"problem_description": "We need AI to screen CVs"},
            "parsed_files_text": [],
        }
        result = await rag_search(state, db=mock_db)

    assert result["is_exact_match"] is True
    assert result["exact_match_project"]["project_name"] == "Talentium"


@pytest.mark.asyncio
async def test_rag_node_unrelated_query_no_exact_match():
    """Test that an unrelated query yields no exact match in rag_search node."""
    from backend.nodes.rag_search import rag_search

    mock_db = AsyncMock()

    with patch(
        "backend.nodes.rag_search.search_similar",
        return_value=[("Problem: Finance", 0.35, {"id": "x", "project_name": "Finance Bot"})]
    ):
        state = {
            "form_data": {
                "problem_description": "Automate financial quarterly reports and tax calculations.",
            },
            "parsed_files_text": [],
        }
        result = await rag_search(state, db=mock_db)

    assert "similar_projects" in result
    assert "is_exact_match" in result
    assert result["is_exact_match"] is False
    assert result["exact_match_project"] is None
    # Score 0.35 < 0.60 threshold → not in similar_projects
    assert len(result["similar_projects"]) == 0
