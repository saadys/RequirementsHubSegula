import pytest
pytestmark = pytest.mark.integration
"""
Test SSE Streaming API Endpoint (POST /api/submissions/stream)
Verifies:
1. Event-stream headers and incremental SSE chunk delivery.
2. Progressive emission of node, score, thinking, token, and complete events.
3. Proper handling and persistence during NEEDS_CLARIFICATION decisions.
"""

import json
import os
import sys
import httpx
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, "/app")


@pytest.mark.asyncio
async def test_streaming_endpoint_incomplete_validation():
    """Verifies that missing fields immediately emit an INCOMPLETE complete event."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as ac:
        payload = {
            "project_name": "Incomplete Stream Test",
            "department": "corporate_support",
            "team_contact_name": "Tester",
            "team_contact_email": "tester@segula.fr",
            "problem_description": "Incomplete submission",
            "current_process": "None",
            "expected_outcome": "None",
            "data_description": "None",
            "deadline_urgency": "low",
        }
        async with ac.stream("POST", "/api/submissions/stream", json=payload, timeout=30.0) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

            assert any(e.get("status") == "INCOMPLETE" for e in events)


@pytest.mark.asyncio
async def test_streaming_endpoint_full_pipeline():
    """Verifies end-to-end SSE pipeline streaming events against live running server."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as ac:
        payload = {
            "project_name": "Automated Document Triage",
            "department": "corporate_support",
            "team_contact_name": "Tahir",
            "team_contact_email": "tahir@segula.fr",
            "problem_description": "We want an automated AI classifier to route incoming support tickets to correct departments",
            "current_process": "Manual triage by helpdesk staff taking 2 hours daily",
            "expected_outcome": "90% automated ticket routing accuracy with sub-second classification",
            "data_description": "50,000 historical support tickets with category labels",
            "deadline_urgency": "medium",
            "department_specific": {
                "service_area": "it",
                "target_users": "helpdesk_staff",
                "has_existing_system": True,
                "estimated_user_count": "50-200"
            }
        }
        async with ac.stream("POST", "/api/submissions/stream", json=payload, timeout=90.0) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            received_event_types = set()
            nodes_visited = []
            final_complete_event = None

            async for line in response.aiter_lines():
                if line.startswith("event: "):
                    received_event_types.add(line[7:].strip())
                elif line.startswith("data: "):
                    data = json.loads(line[6:])
                    if "node" in data and data.get("status") == "complete":
                        nodes_visited.append(data["node"])
                    if "request_id" in data and "status" in data:
                        final_complete_event = data

            assert "node" in received_event_types
            assert "score" in received_event_types
            assert "complete" in received_event_types
            assert "parse_input" in nodes_visited
            assert "rag_search" in nodes_visited
            assert "llm_analyze" in nodes_visited
            assert "deterministic_score" in nodes_visited
            assert final_complete_event is not None
            assert final_complete_event["status"] in ("COMPLETED", "REJECTED", "FAST_TRACK", "NEEDS_CLARIFICATION")


@pytest.mark.asyncio
async def test_streaming_endpoint_clarification_handling():
    """Verifies that when a submission needs clarification, questions are streamed and persisted without error."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as ac:
        # Intentionally moderately vague requirement (feasible AI concept, but needs dataset & format clarification)
        payload = {
            "project_name": "Employee Skills Matching Pilot",
            "department": "corporate_support",
            "team_contact_name": "HR Lead",
            "team_contact_email": "hrlead@segula.fr",
            "problem_description": "We want to match consultants to open automotive client missions automatically based on CV skills",
            "current_process": "Staffing managers manually scan through resume folders taking 4 hours per placement",
            "expected_outcome": "Automated skill matching suggestions for managers",
            "data_description": "We have CVs stored in various PDF and Word formats across network drives, but taxonomy and labels are unstandardized and need clarification",
            "deadline_urgency": "medium",
            "department_specific": {
                "service_area": "hr",
                "target_users": "managers",
                "has_existing_system": False
            }
        }
        async with ac.stream("POST", "/api/submissions/stream", json=payload, timeout=90.0) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            clarification_event = None
            complete_event = None

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if "questions" in data:
                        clarification_event = data
                    if "request_id" in data and "status" in data:
                        complete_event = data

            assert complete_event is not None
            # Verify status is valid and not FAILED
            assert complete_event["status"] != "FAILED"

            # If it entered clarification, verify questions exist and DB has them
            if complete_event["status"] == "NEEDS_CLARIFICATION":
                req_id = complete_event["request_id"]
                get_res = await ac.get(f"/api/submissions/{req_id}")
                assert get_res.status_code == 200
                sub_data = get_res.json()
                assert sub_data["status"] == "NEEDS_CLARIFICATION"
                assert len(sub_data["clarification_questions"]) > 0

                # Test clarification streaming re-evaluation endpoint
                answers_payload = {
                    "answers": [
                        "We have 1,200 PDF resumes with standardized skill sections",
                        "Target precision is 90% and IT department will host the tool on an internal GPU server",
                        "GDPR compliant data storage with anonymized candidate IDs"
                    ]
                }
                async with ac.stream(
                    "POST",
                    f"/api/submissions/{req_id}/clarification/stream",
                    json=answers_payload,
                    timeout=90.0,
                ) as clar_stream_res:
                    assert clar_stream_res.status_code == 200
                    assert "text/event-stream" in clar_stream_res.headers.get("content-type", "")

                    stream_completed = False
                    async for line in clar_stream_res.aiter_lines():
                        if line.startswith("data: "):
                            ev_data = json.loads(line[6:])
                            if ev_data.get("status") in ("COMPLETED", "REJECTED", "FAST_TRACK", "NEEDS_CLARIFICATION"):
                                stream_completed = True

                    assert stream_completed is True


@pytest.mark.asyncio
async def test_streaming_endpoint_emits_queue_status():
    """Verifies that POST /api/submissions/stream emits 'event: queue_status' with processing/queued status."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as ac:
        payload = {
            "project_name": "Queue Status SSE Test",
            "department": "corporate_support",
            "team_contact_name": "Queue Tester",
            "team_contact_email": "queue@segula.fr",
            "problem_description": "Testing queue status event emission",
            "current_process": "Manual queue inspection",
            "expected_outcome": "Automated queue event check",
            "data_description": "Sample test data",
            "deadline_urgency": "low",
        }
        async with ac.stream("POST", "/api/submissions/stream", json=payload, timeout=30.0) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            received_events = []
            current_event = None
            async for line in response.aiter_lines():
                line = line.strip()
                if line.startswith("event:"):
                    current_event = line[6:].strip()
                elif line.startswith("data:") and current_event:
                    data = json.loads(line[5:].strip())
                    received_events.append({"event": current_event, "data": data})

            queue_events = [e for e in received_events if e["event"] == "queue_status"]
            assert len(queue_events) >= 1, "Expected at least 1 queue_status event in SSE stream"
            first_q_event = queue_events[0]["data"]
            assert first_q_event["status"] in ("PROCESSING", "QUEUED")
            assert "active_slots" in first_q_event
            assert "max_slots" in first_q_event


@pytest.mark.asyncio
async def test_async_queue_submission_and_polling():
    """Verifies POST /api/submissions/submit-async and GET /{id}/queue-status for decoupled queuing."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as ac:
        payload = {
            "project_name": "Async Decoupled Queue Test",
            "department": "corporate_support",
            "team_contact_name": "Async Tester",
            "team_contact_email": "async@segula.fr",
            "problem_description": "Testing non-blocking queue submission",
            "current_process": "Manual registration",
            "expected_outcome": "Immediate queue assignment",
            "data_description": "Sample test data",
            "deadline_urgency": "low",
        }
        res = await ac.post("/api/submissions/submit-async", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "request_id" in data
        assert data["status"] in ("PROCESSING", "QUEUED")
        req_id = data["request_id"]

        # Check queue-status endpoint
        q_res = await ac.get(f"/api/submissions/{req_id}/queue-status")
        assert q_res.status_code == 200
        q_data = q_res.json()
        assert q_data["status"] in ("PROCESSING", "QUEUED")
        assert "active_slots" in q_data
        assert "max_slots" in q_data
