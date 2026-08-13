"""
Node: deterministic_score
Responsibility: Pure Python scoring engine to calculate project feasibility.
Evaluates 5 Universal Categorical Pillars, applies non-penalizing RAG boost,
and executes hard Circuit Breaker Veto gates. Zero LLM calls involved.
"""

import logging
from typing import Any

from backend.contracts.state import PipelineState
from backend import config

logger = logging.getLogger(__name__)


def calculate_feasibility_score(
    facts: dict[str, Any] | None, 
    rag_scores: list[float] | None = None,
    is_exact_match: bool = False,
) -> dict[str, Any]:
    """
    Calculate the project feasibility score (0-100) deterministically using the 5-pillar rubric.

    Args:
        facts (dict | None): Categorical fact extraction dict.
        rag_scores (list[float] | None): RAG similarity scores from vector search.
        is_exact_match (bool): Whether exact prior art match occurred.

    Returns:
        dict: Containing 'score', 'percentage', 'sub_scores', 'breakdown', 'veto_triggered', 'veto_reasons', and 'decision'.
    """
    rag_scores = rag_scores or []
    max_rag = max(rag_scores) if rag_scores else 0.0
    exact_threshold = getattr(config, "RAG_EXACT_MATCH_THRESHOLD", 0.75)
    similar_threshold = getattr(config, "RAG_SIMILAR_THRESHOLD", 0.60)
    go_threshold = getattr(config, "SCORE_GO_THRESHOLD", 70)
    nogo_threshold = getattr(config, "SCORE_NOGO_THRESHOLD", 20)

    # 1. Check Fast-Track Bypass
    if is_exact_match or max_rag >= exact_threshold:
        return {
            "score": 95,
            "percentage": 95,
            "sub_scores": {"ai_viability": 30, "data_readiness": 25, "problem_clarity": 20, "integration": 10, "governance": 10},
            "breakdown": {
                "ai_viability": {"score": 30, "max": 30},
                "data_readiness": {"score": 25, "max": 25},
                "problem_clarity": {"score": 20, "max": 20},
                "integration": {"score": 10, "max": 15},
                "governance": {"score": 10, "max": 10},
            },
            "veto_triggered": False,
            "veto_reasons": [],
            "decision": "FAST_TRACK",
        }

    facts = facts or {}
    if not facts:
        return {
            "score": 0,
            "percentage": 0,
            "sub_scores": {"ai_viability": 0, "data_readiness": 0, "problem_clarity": 0, "integration": 0, "governance": 0},
            "breakdown": {},
            "veto_triggered": True,
            "veto_reasons": ["Fact extraction failed"],
            "decision": "NO_GO",
        }

    # Extract categories and reasons safely
    def _get_cat_and_reason(pillar_key: str, fallback_cat: str = "") -> tuple[str, str]:
        obj = facts.get(pillar_key)
        if isinstance(obj, dict):
            return obj.get("category", fallback_cat), obj.get("reason", "")
        return facts.get(f"{pillar_key}_category", fallback_cat), facts.get(f"{pillar_key}_reason", "")

    ai_cat, ai_reason = _get_cat_and_reason("ai_viability")
    data_cat, data_reason = _get_cat_and_reason("data_readiness")
    clarity_cat, clarity_reason = _get_cat_and_reason("problem_clarity")
    integ_cat, integ_reason = _get_cat_and_reason("integration_feasibility")
    if not integ_cat:
        integ_cat, integ_reason = _get_cat_and_reason("integration")
    gov_cat, gov_reason = _get_cat_and_reason("governance_and_safety")
    if not gov_cat:
        gov_cat, gov_reason = _get_cat_and_reason("governance")

    # 2. Point Mapping (Sums to 100 base)
    POINTS_AI = {"HIGHLY_VIABLE": 30, "MARGINAL": 15, "NOT_AI": 0, "IMPOSSIBLE": 0}
    POINTS_DATA = {"READY": 25, "UNLABELED_OR_MESSY": 10, "NONE": 0}
    POINTS_CLARITY = {"CLEAR": 20, "PARTIAL": 10, "CONTRADICTORY": 0, "VAGUE": 0}
    POINTS_INTEGRATION = {"SIMPLE": 15, "MODERATE": 10, "COMPLEX": 5}
    POINTS_GOVERNANCE = {"SAFE": 10, "MODERATE_RISK": 5, "CRITICAL_RISK": 0}

    sub_scores = {
        "ai_viability": POINTS_AI.get(ai_cat, 0),
        "data_readiness": POINTS_DATA.get(data_cat, 0),
        "problem_clarity": POINTS_CLARITY.get(clarity_cat, 0),
        "integration": POINTS_INTEGRATION.get(integ_cat, 0),
        "governance": POINTS_GOVERNANCE.get(gov_cat, 0),
    }

    breakdown = {
        "ai_viability": {"score": sub_scores["ai_viability"], "max": 30, "category": ai_cat, "reason": ai_reason},
        "data_readiness": {"score": sub_scores["data_readiness"], "max": 25, "category": data_cat, "reason": data_reason},
        "problem_clarity": {"score": sub_scores["problem_clarity"], "max": 20, "category": clarity_cat, "reason": clarity_reason},
        "integration": {"score": sub_scores["integration"], "max": 15, "category": integ_cat, "reason": integ_reason},
        "governance": {"score": sub_scores["governance"], "max": 10, "category": gov_cat, "reason": gov_reason},
    }

    total_score = sum(sub_scores.values())

    # Prior Art Non-Penalizing Boost (+5 pts)
    if max_rag >= similar_threshold:
        total_score = min(100, total_score + 5)

    veto_reasons: list[str] = []

    # 3. Circuit Breaker Veto Gates
    if ai_cat in ["NOT_AI", "IMPOSSIBLE"]:
        total_score = min(total_score, 18)
        veto_reasons.append(f"AI Viability VETO: {ai_cat} ({ai_reason})")

    if gov_cat == "CRITICAL_RISK":
        total_score = min(total_score, 10)
        veto_reasons.append(f"Ethical/Security VETO: {gov_reason}")

    if clarity_cat == "CONTRADICTORY":
        total_score = min(total_score, 45)
        veto_reasons.append(f"Contradiction VETO: {clarity_reason}")

    if data_cat == "NONE":
        total_score = min(total_score, 45)
        veto_reasons.append(f"Data VETO: {data_reason}")

    veto_triggered = len(veto_reasons) > 0

    # 4. Final Routing Decision
    if total_score >= go_threshold:
        decision = "GO"
    elif total_score < nogo_threshold:
        decision = "NO_GO"
    else:
        decision = "NEEDS_CLARIFICATION"

    return {
        "score": total_score,
        "percentage": total_score,
        "sub_scores": sub_scores,
        "breakdown": breakdown,
        "veto_triggered": veto_triggered,
        "veto_reasons": veto_reasons,
        "decision": decision,
    }


# Alias requested by user requirement
Score_final = calculate_feasibility_score


def deterministic_score(state: PipelineState) -> dict[str, Any]:
    """
    LangGraph Node function executing the 5-pillar deterministic scoring engine.

    Args:
        state (PipelineState): Current graph state.

    Returns:
        dict: State update dictionary with score, score_breakdown, sub_scores, veto flags, and decision.
    """
    facts = state.get("extracted_facts")
    rag_scores = state.get("rag_scores", [])
    is_exact_match = state.get("is_exact_match", False)

    result = calculate_feasibility_score(facts, rag_scores, is_exact_match=is_exact_match)

    logger.info(
        "5-Pillar deterministic scoring completed | score=%d decision=%s veto_triggered=%s",
        result["score"],
        result["decision"],
        result["veto_triggered"],
    )

    return {
        "score": result["score"],
        "score_breakdown": result["breakdown"],
        "sub_scores": result["sub_scores"],
        "veto_triggered": result["veto_triggered"],
        "veto_reasons": result["veto_reasons"],
        "decision": result["decision"],
    }

