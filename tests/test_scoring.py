import pytest
from backend.nodes.deterministic_score import calculate_feasibility_score, deterministic_score, Score_final


def test_score_final_alias():
    assert Score_final == calculate_feasibility_score


def test_perfect_score_go():
    facts = {
        "ai_viability": {"category": "HIGHLY_VIABLE", "reason": "Clear NLP task"},
        "data_readiness": {"category": "READY", "reason": "10k clean labeled samples"},
        "problem_clarity": {"category": "CLEAR", "reason": "Precise KPIs and inputs/outputs"},
        "integration_feasibility": {"category": "SIMPLE", "reason": "Standalone API"},
        "governance_and_safety": {"category": "SAFE", "reason": "Standard non-sensitive internal data"},
    }
    # Base: 30 + 25 + 20 + 15 + 10 = 100
    result = calculate_feasibility_score(facts, [0.65])
    assert result["score"] == 100
    assert result["decision"] == "GO"
    assert result["veto_triggered"] is False


def test_not_ai_veto_no_go():
    facts = {
        "ai_viability": {"category": "NOT_AI", "reason": "Pure CSV to XML file format conversion"},
        "data_readiness": {"category": "READY", "reason": "CSV files available"},
        "problem_clarity": {"category": "CLEAR", "reason": "Well defined conversion"},
        "integration_feasibility": {"category": "SIMPLE", "reason": "Standalone script"},
        "governance_and_safety": {"category": "SAFE", "reason": "No compliance risks"},
    }
    result = calculate_feasibility_score(facts, [])
    assert result["score"] <= 18
    assert result["decision"] == "NO_GO"
    assert result["veto_triggered"] is True
    assert any("AI Viability VETO" in r for r in result["veto_reasons"])


def test_governance_critical_risk_veto():
    facts = {
        "ai_viability": {"category": "HIGHLY_VIABLE", "reason": "Language model text generation"},
        "data_readiness": {"category": "READY", "reason": "Large text corpus"},
        "problem_clarity": {"category": "CLEAR", "reason": "Clear generation task"},
        "integration_feasibility": {"category": "SIMPLE", "reason": "API endpoint"},
        "governance_and_safety": {"category": "CRITICAL_RISK", "reason": "Phishing and credential harvesting"},
    }
    result = calculate_feasibility_score(facts, [])
    assert result["score"] <= 10
    assert result["decision"] == "NO_GO"
    assert result["veto_triggered"] is True
    assert any("Ethical/Security VETO" in r for r in result["veto_reasons"])


def test_clarification_partial_data():
    facts = {
        "ai_viability": {"category": "HIGHLY_VIABLE", "reason": "CV classification"},
        "data_readiness": {"category": "UNLABELED_OR_MESSY", "reason": "Raw unindexed images"},
        "problem_clarity": {"category": "PARTIAL", "reason": "Vague defect thresholds"},
        "integration_feasibility": {"category": "MODERATE", "reason": "Quality check line"},
        "governance_and_safety": {"category": "SAFE", "reason": "Internal manufacturing"},
    }
    # Score: 30 + 10 + 10 + 10 + 10 = 70. Without high RAG boost, let's test around 50-65:
    facts["integration_feasibility"] = {"category": "COMPLEX", "reason": "Legacy PLC"}
    # Score: 30 + 10 + 10 + 5 + 10 = 65
    result = calculate_feasibility_score(facts, [])
    assert 20 <= result["score"] < 70
    assert result["decision"] == "NEEDS_CLARIFICATION"


def test_deterministic_score_node():
    state = {
        "extracted_facts": {
            "ai_viability": {"category": "HIGHLY_VIABLE", "reason": "NLP search"},
            "data_readiness": {"category": "READY", "reason": "Indexed documents"},
            "problem_clarity": {"category": "CLEAR", "reason": "Clear Q&A use case"},
            "integration_feasibility": {"category": "SIMPLE", "reason": "Web assistant"},
            "governance_and_safety": {"category": "SAFE", "reason": "Public policies"},
        },
        "rag_scores": [0.65],
    }
    update = deterministic_score(state)
    assert update["score"] == 100
    assert update["decision"] == "GO"
    assert "ai_viability" in update["score_breakdown"]
    assert "sub_scores" in update

