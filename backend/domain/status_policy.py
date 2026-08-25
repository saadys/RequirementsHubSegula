"""
Submission Status Policy

Single authority translating a terminal :class:`PipelineState` into the
user-facing ``SubmissionStatus`` persisted on the ``submissions`` row.

Why this module exists
----------------------
This rule previously lived as three byte-identical private copies of
``_determine_status`` in ``routes_submissions.py``, ``routes_clarification.py``
and ``routes_stream.py``. Three copies of one business rule means three places
to update and three ways to drift — the exact failure mode this refactor removes.

Design notes
------------
* **Pure function, no I/O.** Takes a mapping, returns a string. Testable without
  a database, an event loop or a FastAPI client.
* **Mapping, not PipelineState.** Typed as ``Mapping[str, Any]`` rather than
  ``PipelineState`` so callers can pass a LangGraph result dict, a partial state
  or a plain fixture without a cast. ``PipelineState`` is a ``total=False``
  TypedDict, so it satisfies this signature structurally.
* **Reads defensively.** Every access goes through ``.get()``: a state resumed
  from an older checkpoint may predate any field referenced here.
"""

from typing import Any, Mapping

from backend.schemas import Decision, SubmissionStatus

__all__ = ["resolve_submission_status"]


def resolve_submission_status(state: Mapping[str, Any]) -> str:
    """Derives the user-facing submission status from a terminal pipeline state.

    Precedence is deliberate and must not be reordered:

    1. ``missing_fields`` — the request never reached evaluation, so no decision
       taken further down the pipeline can be trusted.
    2. ``is_exact_match`` — the fast-track branch short-circuits scoring entirely;
       any ``decision`` present alongside it is incidental.
    3. ``decision`` — the normal scoring outcome.
    4. ``PROCESSED`` — the pipeline ran but produced no decision. Reaching this
       branch in production indicates an incomplete run, not a nominal outcome.

    Args:
        state: Terminal pipeline state (or any mapping exposing the same keys).

    Returns:
        The ``SubmissionStatus`` value to persist, as a plain ``str``.
    """
    if state.get("missing_fields"):
        return SubmissionStatus.INCOMPLETE.value

    if state.get("is_exact_match"):
        return SubmissionStatus.FAST_TRACK.value

    decision = state.get("decision")

    if decision == Decision.GO.value:
        return SubmissionStatus.COMPLETED.value

    if decision == Decision.NO_GO.value:
        return SubmissionStatus.REJECTED.value

    if decision == Decision.NEEDS_CLARIFICATION.value:
        # A report alongside NEEDS_CLARIFICATION means the clarification budget
        # was exhausted and a partial dossier was issued: the submission is
        # closed, not awaiting an answer that will never be requested.
        if state.get("report"):
            return SubmissionStatus.COMPLETED.value
        return SubmissionStatus.NEEDS_CLARIFICATION.value

    return SubmissionStatus.PROCESSED.value
