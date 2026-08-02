"""
Tests for AI Team Dashboard API Endpoints (Module E)
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_override_decision_not_found():
    """Test 404 for non-existent submission ID when performing decision override."""
    res = client.post(
        "/api/dashboard/invalid_id_888/decision",
        json={
            "decision": "GO",
            "reviewer_notes": "Manual override test",
            "reviewer_name": "Test Engineer",
        },
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_dashboard_pending_and_override():
    """Test listing pending requests and performing a manual decision override by an AI engineer."""
    vague_payload = {
        "project_name": "Low Feasibility Idea",
        "department": "corporate_support",
        "team_contact_name": "Alex Vance",
        "team_contact_email": "alex.vance@segula.fr",
        "problem_description": "General AI idea for productivity without data or specifics.",
        "current_process": "Unknown",
        "expected_outcome": "Automate everything",
        "deadline_urgency": "low",
        "department_specific": {
            "service_area": "hr",
            "target_users": "employees",
            "has_existing_system": False,
        },
    }

    create_res = client.post("/api/submissions/", json=vague_payload)
    assert create_res.status_code == 201
    submission = create_res.json()
    req_id = submission["request_id"]

    # 1. Check Pending List
    pending_res = client.get("/api/dashboard/pending")
    assert pending_res.status_code == 200
    pending_items = pending_res.json()
    assert isinstance(pending_items, list)
    matching = [p for p in pending_items if p["request_id"] == req_id]
    assert len(matching) >= 1

    # 2. Perform AI Engineer Decision Override to GO
    override_payload = {
        "decision": "GO",
        "reviewer_notes": "Approved manually after direct discussion with business team lead.",
        "reviewer_name": "Sarah Connor",
    }
    override_res = client.post(f"/api/dashboard/{req_id}/decision", json=override_payload)
    assert override_res.status_code == 200
    override_data = override_res.json()

    assert override_data["request_id"] == req_id
    assert override_data["decision"] == "GO"
    assert override_data["status"] == "COMPLETED"
    assert override_data["manual_override"] is True
    assert override_data["reviewer_name"] == "Sarah Connor"

    # 3. Verify state persisted via GET /api/submissions/{request_id}
    sub_res = client.get(f"/api/submissions/{req_id}")
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["decision"] == "GO"
    assert sub_data["status"] == "COMPLETED"
