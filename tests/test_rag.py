"""Tests for RAG retrieval accuracy. Owner: Track A"""

import pytest
from backend.services.vectorstore import load_seed_data, search_similar
from backend.nodes.rag_search import rag_search


@pytest.fixture(scope="module", autouse=True)
def setup_seed_data():
    """Ensure vectorstore seed data is loaded into ChromaDB before running RAG tests."""
    load_seed_data()


def test_rag_cv_screening_matches_talentium():
    """Test that CV screening queries match Talentium as the top result."""
    results = search_similar("We need AI to screen CVs and score candidates", top_k=2)
    assert len(results) > 0
    top_doc, top_score, top_meta = results[0]
    assert "Talentium" in top_meta.get("project_name", "")


def test_rag_onboarding_chatbot_matches_irfane():
    """Test that chatbot for onboarding queries match IRFANE as the top result."""
    results = search_similar("chatbot for new employee onboarding and HR search", top_k=2)
    assert len(results) > 0
    top_doc, top_score, top_meta = results[0]
    assert "IRFANE" in top_meta.get("project_name", "")



def test_rag_node_unrelated_query_no_exact_match():
    """Test that an unrelated query yields no exact match in rag_search node."""
    fake_state = {
        "form_data": {
            "project_name": "Finance Automation",
            "department": "corporate_support",
            "problem_description": "Automate financial quarterly reports and tax calculations.",
            "current_process": "Excel manual entry",
            "expected_outcome": "Automated PDF report generation",
        },
        "parsed_files_text": [],
        "department": "corporate_support",
    }
    result = rag_search(fake_state)
    assert "similar_projects" in result
    assert "is_exact_match" in result
    assert result["is_exact_match"] is False
    assert result["exact_match_project"] is None
