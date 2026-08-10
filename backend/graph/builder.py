"""
LangGraph Graph Builder

Constructs and compiles the full pipeline graph by wiring all nodes together.

Owner: TOGETHER (Phase 3 — Integration)
"""

from langgraph.graph import StateGraph, END, START

from backend.contracts.state import PipelineState

# ── Node imports ─────────────────────────────────────────────────
from backend.nodes.parse_input import parse_input
from backend.nodes.validate_completeness import validate_completeness
from backend.nodes.rag_search import rag_search
from backend.nodes.fast_track import fast_track
from backend.nodes.llm_analyze import llm_analyze
from backend.nodes.deterministic_score import deterministic_score
from backend.nodes.generate_questions import generate_questions
from backend.nodes.generate_report import generate_report

# ── Routing imports ──────────────────────────────────────────────
from backend.graph.routing import (
    route_after_validation,
    route_after_rag,
    route_after_score,
)


def build_graph() -> StateGraph:
    """Constructs the full AI Requirement Hub pipeline as a LangGraph StateGraph."""
    graph = StateGraph(PipelineState)

    # ── Add all nodes ────────────────────────────────────────────
    graph.add_node("parse_input", parse_input)
    graph.add_node("validate_completeness", validate_completeness)
    graph.add_node("rag_search", rag_search)
    graph.add_node("fast_track", fast_track)
    graph.add_node("llm_analyze", llm_analyze)
    graph.add_node("deterministic_score", deterministic_score)
    graph.add_node("generate_questions", generate_questions)
    graph.add_node("generate_report", generate_report)

    # ── Wire edges ───────────────────────────────────────────────

    # Entry: START → parse_input → validate_completeness
    graph.add_edge(START, "parse_input")
    graph.add_edge("parse_input", "validate_completeness")

    # After validation: conditional → rag_search or end_incomplete
    graph.add_conditional_edges(
        "validate_completeness",
        route_after_validation,
        {
            "rag_search": "rag_search",
            "end_incomplete": END,
        },
    )

    # After RAG: conditional → fast_track or llm_analyze
    graph.add_conditional_edges(
        "rag_search",
        route_after_rag,
        {
            "fast_track": "fast_track",
            "llm_analyze": "llm_analyze",
        },
    )

    # fast_track → END
    graph.add_edge("fast_track", END)

    # llm_analyze → deterministic_score
    graph.add_edge("llm_analyze", "deterministic_score")

    # After scoring: conditional → generate_report, generate_questions
    graph.add_conditional_edges(
        "deterministic_score",
        route_after_score,
        {
            "generate_report": "generate_report",
            "generate_questions": "generate_questions",
        },
    )

    # generate_report → END
    graph.add_edge("generate_report", END)

    # generate_questions → END (pause for user input; graph is re-invoked later)
    graph.add_edge("generate_questions", END)

    return graph


def get_compiled_graph():
    """Builds and compiles the graph, returning a runnable."""
    graph = build_graph()
    return graph.compile()
