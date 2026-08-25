"""
Unit tests for backend.domain.status_policy.

These run without a database, an event loop or an HTTP client — the point of
extracting the rule into the domain layer is that it becomes testable in
isolation. Each test pins one branch of the documented precedence order so a
future reordering fails loudly instead of silently changing which status the
frontend sees.
"""

import pytest

from backend.domain.status_policy import resolve_submission_status
from backend.schemas import SubmissionStatus


class TestPrecedence:
    """The precedence order documented in resolve_submission_status is load-bearing."""

    def test_missing_fields_wins_over_everything(self):
        # An incomplete request never reached evaluation, so a decision or an
        # exact match sitting alongside it must not be trusted.
        state = {
            "missing_fields": ["data_description"],
            "is_exact_match": True,
            "decision": "GO",
            "report": "# dossier",
        }
        assert resolve_submission_status(state) == SubmissionStatus.INCOMPLETE.value

    def test_exact_match_wins_over_decision(self):
        # fast_track short-circuits scoring; any decision present is incidental.
        state = {"is_exact_match": True, "decision": "NO_GO"}
        assert resolve_submission_status(state) == SubmissionStatus.FAST_TRACK.value


class TestDecisionMapping:
    @pytest.mark.parametrize(
        ("decision", "expected"),
        [
            ("GO", SubmissionStatus.COMPLETED.value),
            ("NO_GO", SubmissionStatus.REJECTED.value),
        ],
    )
    def test_terminal_decisions(self, decision, expected):
        assert resolve_submission_status({"decision": decision}) == expected

    def test_needs_clarification_without_report_stays_open(self):
        state = {"decision": "NEEDS_CLARIFICATION"}
        assert resolve_submission_status(state) == SubmissionStatus.NEEDS_CLARIFICATION.value

    def test_needs_clarification_with_report_is_closed(self):
        # A report alongside NEEDS_CLARIFICATION means the clarification budget
        # was exhausted and a partial dossier was issued: nothing more is awaited.
        state = {"decision": "NEEDS_CLARIFICATION", "report": "# partial dossier"}
        assert resolve_submission_status(state) == SubmissionStatus.COMPLETED.value


class TestDefensiveReads:
    """A state resumed from an older checkpoint may lack any field referenced here."""

    def test_empty_state_falls_back_to_processed(self):
        assert resolve_submission_status({}) == SubmissionStatus.PROCESSED.value

    def test_unknown_decision_falls_back_to_processed(self):
        assert resolve_submission_status({"decision": "MAYBE"}) == SubmissionStatus.PROCESSED.value

    def test_empty_missing_fields_is_not_incomplete(self):
        # An empty list means "validated, nothing missing" — not "incomplete".
        state = {"missing_fields": [], "decision": "GO"}
        assert resolve_submission_status(state) == SubmissionStatus.COMPLETED.value

    def test_falsy_is_exact_match_is_not_fast_track(self):
        state = {"is_exact_match": False, "decision": "GO"}
        assert resolve_submission_status(state) == SubmissionStatus.COMPLETED.value
