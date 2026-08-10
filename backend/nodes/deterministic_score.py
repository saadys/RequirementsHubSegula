"""
Node: deterministic_score
Responsibility: Pure Python scoring engine to calculate project feasibility.
Zero LLM calls involved. Returns score (0-100), breakdown, and GO/NO_GO decision.
"""

import logging
from typing import Any

from backend.contracts.state import PipelineState
from backend import config

logger = logging.getLogger(__name__)


def calculate_feasibility_score(
    facts: dict[str, Any] | None, 
    rag_scores: list[float] | None = None
) -> dict[str, Any]:
    """
    Calculate the project feasibility score (0-100) deterministically.

    Args:
        facts (dict | None): FactExtraction dictionary from llm_analyze node.
        rag_scores (list[float] | None): RAG similarity scores from vector search.

    Returns:
        dict: Containing 'score', 'percentage', 'decision', and 'breakdown'.
    """
    facts = facts or {}
    rag_scores = rag_scores or []

    score = 0
    breakdown: dict[str, dict[str, int]] = {}

    # 1. Problem clarity (Max 20 pts)
    s = 20 if facts.get("has_clear_problem_statement") is True else 0
    breakdown["problem_clarity"] = {"score": s, "max": 20}
    score += s

    # 2. AI solvability (Max 15 pts)
    s = 15 if facts.get("problem_is_ai_solvable") is True else 0
    breakdown["ai_solvability"] = {"score": s, "max": 15}
    score += s

    # 3. Data availability (Max 20 pts)
    data_map = {"none": 0, "partial": 10, "full": 20}
    s = data_map.get(str(facts.get("data_availability")).lower(), 0)
    breakdown["data_availability"] = {"score": s, "max": 20}
    score += s

    # 4. Similar project / Prior Art (Max 15 pts)
    max_rag = max(rag_scores) if rag_scores else 0.0
    exact_threshold = getattr(config, "RAG_EXACT_MATCH_THRESHOLD", 0.75)
    similar_threshold = getattr(config, "RAG_SIMILAR_THRESHOLD", 0.60)
    
    if max_rag >= exact_threshold:
        s = 15  # Exact existing solution
    elif max_rag >= similar_threshold:
        s = 12  # Similar prior art exists
    else:
        s = 5   # Novel project (low penalty)
    breakdown["similar_projects"] = {"score": s, "max": 15}
    score += s

    # 5. Research required (Max 10 pts)
    s = 10 if not facts.get("requires_new_research", False) else 3
    breakdown["research_needed"] = {"score": s, "max": 10}
    score += s

    # 6. Technique identified (Max 10 pts)
    technique = str(facts.get("ai_technique_identified", "unknown")).strip().lower()
    s = 10 if technique and technique != "unknown" else 0
    breakdown["technique_clarity"] = {"score": s, "max": 10}
    score += s

    # 7. Integration complexity (Max 10 pts)
    complexity_map = {"low": 10, "medium": 7, "high": 3}
    s = complexity_map.get(str(facts.get("integration_complexity")).lower(), 5)
    breakdown["integration"] = {"score": s, "max": 10}
    score += s

    # Determine Routing Decision dynamically from config
    go_threshold = getattr(config, "SCORE_GO_THRESHOLD", 70)
    nogo_threshold = getattr(config, "SCORE_NOGO_THRESHOLD", 40)

    if score >= go_threshold:
        decision = "GO"
    elif score >= nogo_threshold:
        decision = "NEEDS_CLARIFICATION"
    else:
        decision = "NO_GO"

    return {
        "score": score,
        "percentage": score,
        "decision": decision,
        "breakdown": breakdown,
    }


# Alias requested by user requirement
Score_final = calculate_feasibility_score


def deterministic_score(state: PipelineState) -> dict[str, Any]:
    """
    LangGraph Node function executing the deterministic scoring engine.

    Args:
        state (PipelineState): Current graph state containing 'extracted_facts' & 'rag_scores'.

    Returns:
        dict: State update dictionary with 'score', 'score_breakdown', and 'decision'.
    """
    facts = state.get("extracted_facts")
    rag_scores = state.get("rag_scores", [])

    result = calculate_feasibility_score(facts, rag_scores)

    logger.info("Deterministic scoring completed | score=%d decision=%s", result["score"], result["decision"])

    return {
        "score": result["score"],
        "score_breakdown": result["breakdown"],
        "decision": result["decision"],
    }
