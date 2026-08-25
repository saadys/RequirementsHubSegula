"""
Submission Mappers

Single authority projecting ``Submission`` ORM entities (and their eagerly
loaded relations) onto the API DTOs ``SubmissionResponse`` and
``ClarificationResponse``.

Why this module exists
----------------------
Three endpoints previously re-derived the same four projections inline:

* which clarification round is the current one,
* whether the clarification loop is closed,
* which questions are still actionable by the requester,
* how a ``ScoringResult.breakdown`` JSON blob flattens into
  ``sub_scores`` / ``veto_triggered`` / ``veto_reasons``.

The three copies were subtly divergent in expression (though equivalent in
outcome, see :func:`project_clarification_view`), which is precisely how a
future edit to one of them would have silently changed one endpoint only.

Design notes
------------
* **Pure and synchronous.** No lazy relationship loading is triggered here:
  callers must hand over entities fetched through ``get_*_with_relations``.
  Keeping this layer free of ``await`` makes an accidental N+1 impossible by
  construction, since a lazy load on a detached async entity raises rather than
  silently issuing per-row queries.
* **Defensive on nullables.** Every relation on ``Submission`` is optional at the
  ORM level (``uselist=False`` 1:1 relations, cascade-deleted collections), so
  each access is guarded.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from backend.config import MAX_CLARIFICATION_ROUNDS
from backend.models.db_schemes.requirementshub.schemes.submission import Submission
from backend.schemas import ClarificationResponse, SubmissionResponse

__all__ = [
    "ClarificationView",
    "ScoringView",
    "build_clarification_response",
    "build_submission_response",
    "project_clarification_view",
    "project_scoring_view",
]

# Statuses that close a submission: reaching any of them means no further
# clarification round will ever be requested, whatever the round counter says.
_TERMINAL_STATUSES: frozenset[str] = frozenset({"COMPLETED", "REJECTED", "FAST_TRACK"})


@dataclass(frozen=True, slots=True)
class ClarificationView:
    """Flattened, decision-ready projection of a submission's clarification rounds."""

    round_number: int
    """Latest round number, or 0 when no round has been opened yet."""

    is_closed: bool
    """True when the clarification loop can no longer accept answers."""

    active_questions: List[Any]
    """Questions still awaiting an answer. Empty once answered or closed."""

    all_answers: List[str]
    """Every answer across every round, in round order."""

    latest_answers: List[str]
    """Answers of the latest round only."""


@dataclass(frozen=True, slots=True)
class ScoringView:
    """Flattened projection of a ``ScoringResult`` and its JSON breakdown."""

    score: Optional[int] = None
    decision: Optional[str] = None
    sub_scores: Dict[str, int] = field(default_factory=dict)
    veto_triggered: bool = False
    veto_reasons: List[str] = field(default_factory=list)


def project_clarification_view(sub: Submission) -> ClarificationView:
    """Projects a submission's clarification rounds into a single decision-ready view.

    Closure rule. The loop is closed when either:

    * the requester has answered the final allowed round
      (``round_number >= MAX_CLARIFICATION_ROUNDS`` *and* answers present), or
    * a report exists and the submission sits in a terminal status.

    Actionable-questions rule. Questions are surfaced only while the loop is
    open *and* the latest round is unanswered. This unifies two expressions that
    were used interchangeably across the previous three call sites::

        [] if (is_closed or has_answered) else questions          # routes A & B
        [] if is_closed else (questions if not answers else [])   # route C

    They are logically equivalent (``not (c or a) == (not c) and (not a)``); this
    function settles on the first form and makes the equivalence a non-issue.

    Args:
        sub: A ``Submission`` with ``clarification_rounds`` and ``report`` loaded.

    Returns:
        The flattened :class:`ClarificationView`.
    """
    rounds = sorted(sub.clarification_rounds or [], key=lambda r: r.round_number)
    latest = rounds[-1] if rounds else None

    round_number = latest.round_number if latest else 0
    latest_answers: List[str] = list(latest.answers or []) if latest else []
    has_answered_latest = bool(latest_answers)

    reached_final_round = round_number >= MAX_CLARIFICATION_ROUNDS
    is_reported_and_terminal = sub.report is not None and sub.status in _TERMINAL_STATUSES
    is_closed = (has_answered_latest and reached_final_round) or is_reported_and_terminal

    active_questions: List[Any] = (
        []
        if (is_closed or has_answered_latest or latest is None)
        else list(latest.questions or [])
    )

    all_answers: List[str] = [answer for r in rounds for answer in (r.answers or [])]

    return ClarificationView(
        round_number=round_number,
        is_closed=is_closed,
        active_questions=active_questions,
        all_answers=all_answers,
        latest_answers=latest_answers,
    )


def project_scoring_view(sub: Submission) -> ScoringView:
    """Projects a submission's scoring result and reviewer overrides into a flat view.

    A reviewer override always wins over the pipeline's own decision: a human
    ruling is authoritative over the automated one. ``score`` is left untouched
    so the original feasibility number stays auditable next to the override.

    ``breakdown`` is read with a ``sub_scores`` / ``pillar_scores`` fallback
    because rows written before the 5-pillar migration use the legacy key.
    """
    scoring = sub.scoring_result
    overrides: Sequence[Any] = sub.reviewer_overrides or []

    decision = overrides[0].new_decision if overrides else (scoring.decision if scoring else None)

    breakdown: Dict[str, Any] = (scoring.breakdown or {}) if scoring else {}

    return ScoringView(
        score=scoring.score if scoring else None,
        decision=decision,
        sub_scores=breakdown.get("sub_scores") or breakdown.get("pillar_scores") or {},
        veto_triggered=bool(breakdown.get("veto_triggered", False)),
        veto_reasons=breakdown.get("veto_reasons") or [],
    )


def _project_form_data(sub: Submission) -> Dict[str, Any]:
    """Rebuilds the original submitted form payload from persisted columns."""
    return {
        "project_name": sub.project_name,
        "department": sub.department_id,
        "team_contact_name": sub.team_contact_name,
        "team_contact_email": sub.team_contact_email,
        "problem_description": sub.problem_description,
        "current_process": sub.current_process,
        "expected_outcome": sub.expected_outcome,
        "data_description": sub.data_description,
        "deadline_urgency": sub.deadline_urgency,
        "department_specific": sub.department_specific or {},
    }


def _isoformat_or_none(value: Any) -> Optional[str]:
    """Serializes a timestamp column defensively.

    SQLite (test fixtures) can hand back a plain ``str`` where PostgreSQL returns
    a ``datetime``, so duck-type on ``isoformat`` rather than the concrete type.
    """
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def build_submission_response(sub: Submission) -> SubmissionResponse:
    """Maps a ``Submission`` and its loaded relations onto ``SubmissionResponse``.

    Args:
        sub: A ``Submission`` fetched with all relations eagerly loaded.

    Returns:
        The wire-level DTO returned by the submissions endpoints.
    """
    clarification = project_clarification_view(sub)
    scoring = project_scoring_view(sub)
    fact = sub.fact_extraction
    report = sub.report

    return SubmissionResponse(
        request_id=str(sub.id),
        status=sub.status,
        decision=scoring.decision,
        score=scoring.score,
        sub_scores=scoring.sub_scores,
        veto_triggered=scoring.veto_triggered,
        veto_reasons=scoring.veto_reasons,
        report_type=report.report_type if report else None,
        missing_fields=(fact.extracted_requirements if (fact and fact.extracted_requirements) else []),
        clarification_questions=clarification.active_questions,
        clarification_round=clarification.round_number,
        max_rounds=MAX_CLARIFICATION_ROUNDS,
        parsed_files_text=sub.parsed_files_text or [],
        report=report.content if report else None,
        created_at=_isoformat_or_none(sub.created_at),
        form_data=_project_form_data(sub),
    )


def build_clarification_response(sub: Submission) -> ClarificationResponse:
    """Maps a ``Submission`` and its loaded relations onto ``ClarificationResponse``.

    ``answers`` falls back to the latest round's answers when the cross-round
    aggregate is empty, preserving the behaviour the clarification endpoints
    already exposed to the frontend.
    """
    clarification = project_clarification_view(sub)
    scoring = project_scoring_view(sub)
    report = sub.report

    return ClarificationResponse(
        request_id=str(sub.id),
        status=sub.status,
        clarification_round=clarification.round_number,
        max_rounds=MAX_CLARIFICATION_ROUNDS,
        questions=clarification.active_questions,
        answers=clarification.all_answers or clarification.latest_answers,
        score=scoring.score,
        decision=scoring.decision,
        sub_scores=scoring.sub_scores,
        veto_triggered=scoring.veto_triggered,
        veto_reasons=scoring.veto_reasons,
        report_type=report.report_type if report else None,
        report=report.content if report else None,
    )
