"""
Pipeline State Definition

The TypedDict that flows through every LangGraph node.
Track A writes to some fields, Track B reads them (and vice versa).

⚠️  SHARED FILE — Do not edit without agreement from both engineers.

⚠️  CHECKPOINTED — this graph runs with a Postgres checkpointer (see
backend/graph/builder.py / backend/main.py), so old threads paused at
await_clarification_answers get deserialized straight into this shape on
resume, potentially long after a new field was added here. Every node MUST
read fields with state.get(key, default) — never state[key] — or a resumed
thread from before the field existed will KeyError in production.
"""

from typing import TypedDict


class PipelineState(TypedDict, total=False):
    # ── Input (set by API route before graph starts) ──────────────
    request_id: str                          # UUID for this submission
    form_data: dict                          # Raw form fields
    department: str                          # e.g. "corporate_support"
    uploaded_files: list[str]                # File paths on disk

    # ── Parse & Validate (Track B writes, others read) ────────────
    parsed_files_text: list[str]             # Extracted text from files
    missing_fields: list[str]                # Empty list = complete
    is_complete: bool

    # ── RAG (Track A writes, scoring reads) ───────────────────────
    similar_projects: list[dict]             # Top-K results from ChromaDB
    rag_scores: list[float]                  # Similarity scores
    is_exact_match: bool                     # Any score >= 0.95?
    exact_match_project: dict | None         # The matched project if exact

    # ── LLM Analysis (Track A writes, Track B scoring reads) ─────
    extracted_facts: dict | None             # FactExtraction as dict
    extracted_facts_model_used: str | None   # Model that actually produced extracted_facts (may differ from PRIMARY_MODEL after fallback)

    # ── Clarification (both tracks interact) ─────────────────────
    clarification_round: int                 # Starts at 0, max 2
    clarification_questions: list[str]       # AI-generated questions
    clarification_answers: list[str]         # Team's answers
    clarification_model_used: str | None     # Model that actually generated clarification_questions

    # ── Scoring (Track B writes, report reads) ───────────────────
    score: int                               # 0-100
    score_breakdown: dict                    # Per-criterion / Per-pillar scores
    sub_scores: dict                         # 5-Pillar scores {"ai_viability": x, ...}
    veto_triggered: bool                     # Whether circuit breaker veto fired
    veto_reasons: list[str]                  # List of active veto reasons
    decision: str                            # "GO" | "NO_GO" | "NEEDS_CLARIFICATION"

    # ── Output (Track B writes) ──────────────────────────────────
    report: str                              # Final cahier de charge (markdown)
    report_type: str                         # "go" | "no_go" | "partial" | "fast_track"
