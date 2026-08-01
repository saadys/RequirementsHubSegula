"""
Conditional Routing Functions

Determines which node to execute next based on the current pipeline state.

Owner: TOGETHER (Phase 3 — Integration)
"""

from backend.contracts.state import PipelineState
from backend import config


def route_after_validation(state: PipelineState) -> str:
    """After validate_completeness: proceed to RAG or stop if incomplete."""
    missing = state.get("missing_fields", [])
    if missing:
        return "end_incomplete"
    return "rag_search"


def route_after_rag(state: PipelineState) -> str:
    """After rag_search: fast-track if exact match, else full LLM analysis."""
    if state.get("is_exact_match", False):
        return "fast_track"
    return "llm_analyze"


def route_after_score(state: PipelineState) -> str:
    """After deterministic_score: route to report, questions, or partial report."""
    decision = state.get("decision", "NO_GO")
    clarification_round = state.get("clarification_round", 0)
    max_rounds = getattr(config, "MAX_CLARIFICATION_ROUNDS", 2)

    if decision == "GO":
        return "generate_report"
    elif decision == "NO_GO":
        return "generate_report"
    else:  # NEEDS_CLARIFICATION
        if clarification_round < max_rounds:
            return "generate_questions"
        # Exhausted clarification rounds — produce partial report
        return "generate_report"
