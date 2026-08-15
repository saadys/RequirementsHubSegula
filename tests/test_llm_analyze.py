"""Tests for LLM structured output extraction (5 Pillars). Owner: Track A"""

import pytest
from backend.nodes.llm_analyze import llm_analyze


def test_llm_analyze_valid_fact_extraction():
    """Test that llm_analyze produces a valid CategoricalFactExtraction dictionary for realistic input."""
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
        "similar_projects": [],
        "rag_scores": [],
    }

    # Run LLM analyze
    result = llm_analyze(state)
    assert "extracted_facts" in result
    facts = result["extracted_facts"]
    assert facts is not None

    # Check 5 Pillars
    assert "ai_viability" in facts
    assert facts["ai_viability"]["category"] in ["HIGHLY_VIABLE", "MARGINAL", "NOT_AI", "IMPOSSIBLE"]
    assert len(facts["ai_viability"]["reason"]) > 0

    assert "data_readiness" in facts
    assert facts["data_readiness"]["category"] in ["READY", "UNLABELED_OR_MESSY", "NONE"]
    assert len(facts["data_readiness"]["reason"]) > 0

    assert "problem_clarity" in facts
    assert facts["problem_clarity"]["category"] in ["CLEAR", "PARTIAL", "CONTRADICTORY", "VAGUE"]
    assert len(facts["problem_clarity"]["reason"]) > 0

    assert "integration_feasibility" in facts
    assert facts["integration_feasibility"]["category"] in ["SIMPLE", "MODERATE", "COMPLEX"]

    assert "governance_and_safety" in facts
    assert facts["governance_and_safety"]["category"] in ["SAFE", "MODERATE_RISK", "CRITICAL_RISK"]

    assert "identified_technique" in facts
    assert "project_summary" in facts
    assert len(facts["project_summary"]) > 5

