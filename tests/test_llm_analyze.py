"""Tests for LLM structured output extraction. Owner: Track A"""

import pytest
from backend.services.vectorstore import load_seed_data
from backend.nodes.rag_search import rag_search
from backend.nodes.llm_analyze import llm_analyze


@pytest.fixture(scope="module", autouse=True)
def setup_seed_data():
    """Ensure vectorstore seed data is loaded before running tests."""
    load_seed_data()


def test_llm_analyze_valid_fact_extraction():
    """Test that llm_analyze produces a valid FactExtraction dictionary for realistic input."""
    state = {
        "form_data": {
            "project_name": "Smart Onboarding Bot",
            "department": "corporate_support",
            "problem_description": "New employees spend 2 weeks asking colleagues basic HR questions. We want an AI chatbot.",
            "current_process": "Manual: ask colleagues or search SharePoint",
            "expected_outcome": "Chatbot that answers HR questions in under 10 seconds",
            "data_description": "We have 500 HR policy documents and an FAQ list",
        },
        "parsed_files_text": [],
        "department": "corporate_support",
        "clarification_round": 0,
        "clarification_answers": [],
    }

    # Run RAG search first to populate similar_projects & rag_scores
    state.update(rag_search(state))

    # Run LLM analyze
    result = llm_analyze(state)
    assert "extracted_facts" in result
    facts = result["extracted_facts"]
    assert facts is not None

    # Check field types & values
    assert isinstance(facts["has_clear_problem_statement"], bool)
    assert facts["has_clear_problem_statement"] is True

    assert isinstance(facts["problem_is_ai_solvable"], bool)
    assert facts["problem_is_ai_solvable"] is True

    allowed_categories = [
        "classification", "regression", "clustering", "nlp",
        "computer_vision", "time_series", "recommendation",
        "optimization", "generative", "other", "unknown"
    ]
    assert facts["problem_category"] in allowed_categories
    assert facts["problem_category"] == "nlp"

    assert facts["data_availability"] in ["none", "partial", "full"]
    assert facts["data_availability"] == "full"

    assert isinstance(facts["ai_technique_identified"], str)
    assert len(facts["ai_technique_identified"]) > 0

    assert isinstance(facts["extracted_requirements"], list)
    assert len(facts["extracted_requirements"]) > 0

    assert isinstance(facts["risks_identified"], list)
    assert isinstance(facts["summary"], str)
    assert len(facts["summary"]) > 10
