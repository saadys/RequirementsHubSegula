"""
tests/test_llm_model_tracking.py
Unit and Integration tests for llm_model_used tracking during streaming and DB persistence.
"""

import uuid
from typing import Any, AsyncIterator, Dict, List, Optional, Type
from pydantic import BaseModel, Field
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.LLM.LLMInterfaces import LLMInterface, T
from backend.LLM.providers.fallback_provider import FallbackLLMProvider
from backend.models.FactExtractionModel import FactExtractionModel
from backend.models.ClarificationModel import ClarificationModel
from backend.models.SubmissionModel import SubmissionModel
from backend.models.db_schemes.requirementshub.schemes import Submission, Department
from backend.api.routes_stream import _save_pipeline_state_to_db


class DummySchema(BaseModel):
    summary: str = Field(description="Summary")


class MockStreamingProvider(LLMInterface):
    def __init__(self, model_name: str, should_fail: bool = False):
        self.model_name = model_name
        self.should_fail = should_fail
        self.last_model_used: Optional[str] = None

    async def generate_text(self, *args, **kwargs) -> str:
        if self.should_fail:
            raise RuntimeError("Primary simulated failure")
        self.last_model_used = self.model_name
        return "response"

    async def generate_text_stream(self, *args, **kwargs) -> AsyncIterator[Dict[str, str]]:
        if self.should_fail:
            raise RuntimeError("Primary stream failed")
        for chunk in ["chunk1", "chunk2"]:
            self.last_model_used = self.model_name
            yield {"type": "token", "content": chunk}

    async def generate_structured_output(self, *args, **kwargs) -> Any:
        if self.should_fail:
            raise RuntimeError("Primary structured failed")
        self.last_model_used = self.model_name
        return DummySchema(summary="done")

    async def generate_structured_output_stream(
        self, prompt: Any, response_schema: Type[T], *args, **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        if self.should_fail:
            raise RuntimeError("Primary structured stream failed")
        # Step 1: yield thinking
        yield {"type": "thinking", "content": "Analyzing..."}
        # Step 2: update model and yield result
        self.last_model_used = self.model_name
        yield {"type": "result", "data": DummySchema(summary="Structured fact data")}

    def health_check(self) -> bool:
        return not self.should_fail


@pytest.mark.asyncio
async def test_fallback_provider_stream_tracking_during_iteration():
    """Verify that last_model_used is updated DURING stream iteration, not just after completion."""
    primary = MockStreamingProvider(model_name="primary-mock-model")
    fallback = MockStreamingProvider(model_name="fallback-mock-model")
    wrapper = FallbackLLMProvider(primary_provider=primary, fallback_provider=fallback)

    captured_model_at_result_event = None

    async for event in wrapper.generate_structured_output_stream(
        prompt="Test",
        response_schema=DummySchema,
    ):
        if event.get("type") == "result":
            # This simulates what stream_llm_analyze does
            captured_model_at_result_event = getattr(wrapper, "last_model_used", None)

    assert captured_model_at_result_event == "primary-mock-model"
    assert wrapper.last_model_used == "primary-mock-model"


@pytest.mark.asyncio
async def test_fallback_provider_stream_tracking_on_failover():
    """Verify that last_model_used reflects the secondary provider when primary fails during stream."""
    primary = MockStreamingProvider(model_name="broken-primary", should_fail=True)
    fallback = MockStreamingProvider(model_name="working-fallback")
    wrapper = FallbackLLMProvider(primary_provider=primary, fallback_provider=fallback)

    captured_model_at_result_event = None

    async for event in wrapper.generate_structured_output_stream(
        prompt="Test",
        response_schema=DummySchema,
    ):
        if event.get("type") == "result":
            captured_model_at_result_event = getattr(wrapper, "last_model_used", None)

    assert captured_model_at_result_event == "working-fallback"
    assert wrapper.last_model_used == "working-fallback"


@pytest.mark.asyncio
async def test_clarification_model_create_or_update_llm_model(
    db_session: AsyncSession, seeded_department: Department
):
    """Verify that ClarificationModel.create_or_update persists llm_model_used correctly."""
    sub_model = SubmissionModel(db_client=db_session)
    sub = await sub_model.create_submission(
        Submission(project_name="Clarification Model Test", department_id=seeded_department.id)
    )

    clar_model = ClarificationModel(db_client=db_session)

    # 1. Create round with llm_model_used
    round_1 = await clar_model.create_or_update(
        submission_id=sub.id,
        round_number=1,
        questions=["Question 1"],
        answers=["Answer 1"],
        llm_model_used="gemini/gemini-3.1-flash-lite",
        auto_commit=True,
    )
    assert round_1.llm_model_used == "gemini/gemini-3.1-flash-lite"

    # 2. Update existing round
    round_1_updated = await clar_model.create_or_update(
        submission_id=sub.id,
        round_number=1,
        questions=["Question 1", "Question 2"],
        answers=["Answer 1"],
        llm_model_used="openai/gpt-4o",
        auto_commit=True,
    )
    assert round_1_updated.llm_model_used == "openai/gpt-4o"
    assert len(round_1_updated.questions) == 2


@pytest.mark.asyncio
async def test_stream_pipeline_db_persistence_with_llm_model(
    db_session: AsyncSession, seeded_department: Department
):
    """Verify that _save_pipeline_state_to_db persists llm_model_used in fact_extractions and clarification_rounds."""
    sub_model = SubmissionModel(db_client=db_session)
    sub = await sub_model.create_submission(
        Submission(project_name="Streaming DB Persistence Test", department_id=seeded_department.id)
    )
    req_id = str(sub.id)

    state = {
        "request_id": req_id,
        "extracted_facts": {
            "ai_viability": {"category": "HIGHLY_VIABLE", "reason": "Standard classification task"},
            "project_summary": "Auto document classification",
        },
        "extracted_facts_model_used": "ollama/qwen2.5:7b",
        "clarification_questions": [{"question": "Data volume?", "target_pillar": "data_readiness"}],
        "clarification_round": 1,
        "clarification_answers": [],
        "clarification_model_used": "ollama/qwen2.5:7b",
        "score": 65,
        "decision": "NEEDS_CLARIFICATION",
        "sub_scores": {"problem_clarity": 15},
    }

    # Call the streaming persistence function
    await _save_pipeline_state_to_db(req_id, state, "NEEDS_CLARIFICATION")

    # Read back and assert
    fact_model = FactExtractionModel(db_client=db_session)
    facts = await fact_model.get_by_submission_id(sub.id)
    assert facts is not None
    assert facts.llm_model_used == "ollama/qwen2.5:7b"
    assert facts.project_summary == "Auto document classification"

    clar_model = ClarificationModel(db_client=db_session)
    rounds = await clar_model.get_rounds_by_submission_id(sub.id)
    assert len(rounds) == 1
    assert rounds[0].round_number == 1
    assert rounds[0].llm_model_used == "ollama/qwen2.5:7b"


@pytest.mark.asyncio
async def test_live_gemini_stream_llm_analyze_and_persistence(
    db_session: AsyncSession, seeded_department: Department
):
    """Real Live E2E test using the actual configured Gemini API key to stream facts and persist to DB."""
    from backend import config
    from backend.nodes.llm_analyze import stream_llm_analyze

    if not config.GEMINI_API_KEY_1:
        pytest.skip("No real GEMINI_API_KEY configured in .env")

    sub_model = SubmissionModel(db_client=db_session)
    sub = await sub_model.create_submission(
        Submission(
            project_name="Predictive Maintenance AI Pilot",
            department_id=seeded_department.id,
            problem_description="We want an anomaly detection model analyzing CNC vibration sensor data in real-time.",
            current_process="Manual inspection every 24 hours leading to unexpected line stoppages.",
            expected_outcome="95% recall on early bearing fault detection 2 hours prior to breakdown.",
            data_description="Time-series vibration data sampled at 10kHz from 40 factory sensors over 6 months.",
            deadline_urgency="high",
            status="IN_PROGRESS",
        )
    )
    req_id = str(sub.id)

    state = {
        "request_id": req_id,
        "department": seeded_department.id,
        "form_data": {
            "project_name": "Predictive Maintenance AI Pilot",
            "problem_description": "We want an anomaly detection model analyzing CNC vibration sensor data in real-time.",
            "current_process": "Manual inspection every 24 hours leading to unexpected line stoppages.",
            "expected_outcome": "95% recall on early bearing fault detection 2 hours prior to breakdown.",
            "data_description": "Time-series vibration data sampled at 10kHz from 40 factory sensors over 6 months.",
            "deadline_urgency": "high",
        },
        "uploaded_files": [],
        "parsed_files_text": [],
        "clarification_round": 0,
        "clarification_answers": [],
    }

    result_payload = None
    captured_model = None

    try:
        async for item in stream_llm_analyze(state):
            if item.get("type") == "result":
                result_payload = item.get("data", {})
                captured_model = result_payload.get("extracted_facts_model_used")
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
            pytest.skip(f"Gemini quota exhausted during live test: {e}")
        raise

    assert result_payload is not None
    assert captured_model is not None
    assert "gemini" in captured_model.lower()

    state.update(result_payload)
    state["score"] = 92
    state["decision"] = "GO"

    await _save_pipeline_state_to_db(req_id, state, "COMPLETED")

    fact_model = FactExtractionModel(db_client=db_session)
    saved_facts = await fact_model.get_by_submission_id(sub.id)
    assert saved_facts is not None
    assert saved_facts.llm_model_used == captured_model
    assert saved_facts.ai_viability_category is not None

