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


# ── Unit tests: ingest_project service ────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_project_service_success():
    """Verifies ingest_project builds rich doc, embeds, merges to DB, and updates Submission status."""
    from backend.services.vectorstore import ingest_project
    from backend.schemas import HistoricProjectIngestInput

    mock_db = AsyncMock()
    mock_submission = MagicMock()
    mock_submission.status = "COMPLETED"
    mock_db.get.return_value = mock_submission

    # Mock merge to return the passed entity
    def fake_merge(record):
        return record

    mock_db.merge.side_effect = fake_merge

    input_data = HistoricProjectIngestInput(
        project_name="Predictive Maintenance for High-Speed Turbines",
        department="aerospace",
        problem_description="Turbine vibration data needs early fault detection.",
        solution_description="Deployed 1D-CNN + LSTM on vibration sensors with edge inference.",
        outcome="Detected bearing failures 48 hours in advance with 97.8% precision.",
        contact_person="Dr. Alex Vance",
        year=2026,
        ai_techniques=["1D-CNN", "LSTM", "Time-Series", "PyTorch"],
        tags=["aerospace", "predictive_maintenance", "vibration", "edge"],
        lessons_learned="High-frequency sampling required downsampling to 1kHz for edge model.",
    )

    with patch("backend.services.vectorstore.generate_embedding", return_value=[0.05] * 768) as mock_embed:
        record, historic_id = await ingest_project(
            submission_id="d3b07384-d113-46fb-a0e0-c8f936173001",
            project_data=input_data,
            db=mock_db,
        )

    assert historic_id.startswith("HIST-2026-")
    assert record.project_name == "Predictive Maintenance for High-Speed Turbines"
    assert record.department == "aerospace"
    assert len(record.embedding) == 768
    assert mock_submission.status == "IMPLEMENTED"
    assert mock_db.commit.called
    assert mock_embed.called

    # Verify doc_string sent to embedder
    embedded_text = mock_embed.call_args[0][0]
    assert "Predictive Maintenance for High-Speed Turbines" in embedded_text
    assert "1D-CNN" in embedded_text
    assert "Lessons Learned: High-frequency sampling" in embedded_text
