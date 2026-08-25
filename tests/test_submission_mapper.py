"""
Unit tests for backend.mappers.submission_mapper.

Built on lightweight stand-ins rather than real ORM instances: the mapper is
deliberately a pure, synchronous projection, so it only needs objects exposing
the same attributes. This keeps the tests free of a database and proves the
mapper never triggers a lazy load (a real detached entity would raise instead).
"""

from types import SimpleNamespace

import pytest

from backend.config import MAX_CLARIFICATION_ROUNDS
from backend.mappers.submission_mapper import (
    build_clarification_response,
    project_clarification_view,
    project_scoring_view,
)


def make_round(round_number, questions=None, answers=None):
    return SimpleNamespace(
        round_number=round_number,
        questions=questions if questions is not None else [],
        answers=answers if answers is not None else [],
    )


def make_submission(
    *,
    status="NEEDS_CLARIFICATION",
    rounds=None,
    report=None,
    scoring=None,
    overrides=None,
):
    return SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        status=status,
        project_name="Invoice OCR",
        department_id="corporate_support",
        team_contact_name="Ada",
        team_contact_email="ada@example.com",
        problem_description="p",
        current_process="c",
        expected_outcome="e",
        data_description="d",
        deadline_urgency="low",
        department_specific={},
        parsed_files_text=[],
        created_at=None,
        clarification_rounds=rounds if rounds is not None else [],
        report=report,
        scoring_result=scoring,
        reviewer_overrides=overrides if overrides is not None else [],
        fact_extraction=None,
    )


class TestClarificationView:
    def test_no_rounds_yields_zero_and_open_loop(self):
        view = project_clarification_view(make_submission())
        assert view.round_number == 0
        assert view.is_closed is False
        assert view.active_questions == []
        assert view.all_answers == []

    def test_unanswered_round_surfaces_its_questions(self):
        sub = make_submission(rounds=[make_round(1, questions=["Q1", "Q2"])])
        view = project_clarification_view(sub)
        assert view.round_number == 1
        assert view.is_closed is False
        assert view.active_questions == ["Q1", "Q2"]

    def test_answered_round_hides_questions_without_closing_the_loop(self):
        # Answered but below the cap: the loop stays open for a further round,
        # yet the answered questions must not be re-presented to the requester.
        sub = make_submission(rounds=[make_round(1, questions=["Q1"], answers=["A1"])])
        view = project_clarification_view(sub)
        assert view.active_questions == []
        assert view.is_closed is (1 >= MAX_CLARIFICATION_ROUNDS)

    def test_answered_final_round_closes_the_loop(self):
        rounds = [
            make_round(n, questions=[f"Q{n}"], answers=[f"A{n}"])
            for n in range(1, MAX_CLARIFICATION_ROUNDS + 1)
        ]
        view = project_clarification_view(make_submission(rounds=rounds))
        assert view.is_closed is True
        assert view.active_questions == []

    def test_report_in_terminal_status_closes_the_loop(self):
        sub = make_submission(
            status="COMPLETED",
            rounds=[make_round(1, questions=["Q1"])],
            report=SimpleNamespace(report_type="go", content="# done"),
        )
        view = project_clarification_view(sub)
        assert view.is_closed is True
        assert view.active_questions == []

    def test_report_in_non_terminal_status_does_not_close_the_loop(self):
        sub = make_submission(
            status="NEEDS_CLARIFICATION",
            rounds=[make_round(1, questions=["Q1"])],
            report=SimpleNamespace(report_type="partial", content="# wip"),
        )
        assert project_clarification_view(sub).is_closed is False

    def test_rounds_are_sorted_before_the_latest_is_picked(self):
        # Guards the fix applied to the clarification POST handler, which read an
        # unsorted collection and could therefore surface a stale round.
        out_of_order = [
            make_round(2, questions=["Q2"]),
            make_round(1, questions=["Q1"], answers=["A1"]),
        ]
        view = project_clarification_view(make_submission(rounds=out_of_order))
        assert view.round_number == 2
        assert view.active_questions == ["Q2"]

    def test_answers_are_aggregated_across_rounds_in_order(self):
        rounds = [
            make_round(2, answers=["A2"]),
            make_round(1, answers=["A1a", "A1b"]),
        ]
        view = project_clarification_view(make_submission(rounds=rounds))
        assert view.all_answers == ["A1a", "A1b", "A2"]
        assert view.latest_answers == ["A2"]

    def test_none_collections_are_tolerated(self):
        sub = make_submission(rounds=None)
        sub.clarification_rounds = None
        view = project_clarification_view(sub)
        assert view.round_number == 0
        assert view.active_questions == []


class TestScoringView:
    def test_absent_scoring_yields_empty_view(self):
        view = project_scoring_view(make_submission())
        assert view.score is None
        assert view.decision is None
        assert view.sub_scores == {}
        assert view.veto_triggered is False
        assert view.veto_reasons == []

    def test_breakdown_is_flattened(self):
        scoring = SimpleNamespace(
            score=72,
            decision="GO",
            breakdown={
                "sub_scores": {"ai_viability": 30},
                "veto_triggered": True,
                "veto_reasons": ["no data"],
            },
        )
        view = project_scoring_view(make_submission(scoring=scoring))
        assert view.score == 72
        assert view.decision == "GO"
        assert view.sub_scores == {"ai_viability": 30}
        assert view.veto_triggered is True
        assert view.veto_reasons == ["no data"]

    def test_legacy_pillar_scores_key_is_honoured(self):
        scoring = SimpleNamespace(
            score=50, decision="NEEDS_CLARIFICATION", breakdown={"pillar_scores": {"data_readiness": 10}}
        )
        assert project_scoring_view(make_submission(scoring=scoring)).sub_scores == {"data_readiness": 10}

    def test_reviewer_override_wins_over_pipeline_decision(self):
        # A human ruling is authoritative; score stays untouched so the original
        # feasibility number remains auditable next to the override.
        scoring = SimpleNamespace(score=35, decision="NO_GO", breakdown={})
        overrides = [SimpleNamespace(new_decision="GO")]
        view = project_scoring_view(make_submission(scoring=scoring, overrides=overrides))
        assert view.decision == "GO"
        assert view.score == 35

    def test_null_breakdown_is_tolerated(self):
        scoring = SimpleNamespace(score=10, decision="NO_GO", breakdown=None)
        view = project_scoring_view(make_submission(scoring=scoring))
        assert view.sub_scores == {}
        assert view.veto_reasons == []


class TestClarificationResponse:
    def test_answers_fall_back_to_latest_round(self):
        # all_answers is empty only when no round carries answers, in which case
        # latest_answers is empty too — the fallback must not fabricate content.
        sub = make_submission(rounds=[make_round(1, questions=["Q1"])])
        resp = build_clarification_response(sub)
        assert resp.answers == []
        assert resp.questions == ["Q1"]
        assert resp.max_rounds == MAX_CLARIFICATION_ROUNDS

    def test_report_fields_are_projected(self):
        sub = make_submission(
            status="COMPLETED",
            report=SimpleNamespace(report_type="go", content="# dossier"),
        )
        resp = build_clarification_response(sub)
        assert resp.report_type == "go"
        assert resp.report == "# dossier"
