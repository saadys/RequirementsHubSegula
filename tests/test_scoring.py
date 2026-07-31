import pytest
from backend.nodes.deterministic_score import calculate_feasibility_score, deterministic_score, Score_final


def test_score_final_alias():
    assert Score_final == calculate_feasibility_score


def test_perfect_score_go():
    facts = {
        "has_clear_problem_statement": True,
        "problem_is_ai_solvable": True,
        "data_availability": "full",
        "requires_new_research": False,
        "ai_technique_identified": "classification",
        "integration_complexity": "low",
    }
    result = calculate_feasibility_score(facts, [0.98])
    assert result["score"] == 100
    assert result["decision"] == "GO"


def test_worst_score_no_go():
    facts = {
        "has_clear_problem_statement": False,
        "problem_is_ai_solvable": False,
        "data_availability": "none",
        "requires_new_research": True,
        "ai_technique_identified": "unknown",
        "integration_complexity": "high",
    }
    result = calculate_feasibility_score(facts, [0.10])
    # Scores: 0 + 0 + 0 + 5 + 3 + 0 + 3 = 11
    assert result["score"] == 11
    assert result["decision"] == "NO_GO"


def test_threshold_clarification():
    facts = {
        "has_clear_problem_statement": True,   # 20
        "problem_is_ai_solvable": True,       # 15
        "data_availability": "partial",       # 10
        "requires_new_research": True,         # 3
        "ai_technique_identified": "unknown", # 0
        "integration_complexity": "medium",    # 7
    }
    # Score: 20 + 15 + 10 + 5 (rag < 0.60) + 3 + 0 + 7 = 60
    result = calculate_feasibility_score(facts, [])
    assert result["score"] == 60
    assert result["decision"] == "NEEDS_CLARIFICATION"


def test_deterministic_score_node():
    state = {
        "extracted_facts": {
            "has_clear_problem_statement": True,
            "problem_is_ai_solvable": True,
            "data_availability": "full",
            "requires_new_research": False,
            "ai_technique_identified": "nlp",
            "integration_complexity": "low",
        },
        "rag_scores": [0.96],
    }
    update = deterministic_score(state)
    assert update["score"] == 100
    assert update["decision"] == "GO"
    assert "problem_clarity" in update["score_breakdown"]
