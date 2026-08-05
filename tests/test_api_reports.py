"""
Tests for Reports & Scores API Endpoints (Module D)
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_get_report_and_score_not_found():
    """Test 404 for non-existent submission IDs."""
    rep_res = client.get("/api/submissions/invalid_req_000/report")
    assert rep_res.status_code == 404
    assert "not found" in rep_res.json()["detail"].lower()

    score_res = client.get("/api/submissions/invalid_req_000/score")
    assert score_res.status_code == 404
    assert "not found" in score_res.json()["detail"].lower()


def test_get_report_and_score_success():
    """Test fetching report and score breakdown endpoints."""
    from backend.services.storage import save_submission

    req_id = "test-report-req-100"
    mock_state = {
        "request_id": req_id,
        "status": "COMPLETED",
        "decision": "GO",
        "score": 85,
        "report_type": "FULL_CAHIER_DES_CHARGES",
        "report": "# AI Document Classifier Feasibility Report\nStatus: GO\nScore: 85/100",
        "score_breakdown": {
            "problem_clarity": {"score": 20, "max": 20},
            "ai_solvability": {"score": 15, "max": 15},
            "data_availability": {"score": 20, "max": 20},
            "similar_projects": {"score": 10, "max": 15},
            "research_needed": {"score": 10, "max": 10},
            "technique_clarity": {"score": 10, "max": 10},
            "integration": {"score": 0, "max": 10},
        },
    }
    save_submission(req_id, mock_state)

    # 1. Fetch Report
    report_res = client.get(f"/api/submissions/{req_id}/report")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["request_id"] == req_id
    assert report_data["is_available"] is True
    assert report_data["report_type"] == "FULL_CAHIER_DES_CHARGES"
    assert len(report_data["report"]) > 20

    # 2. Fetch Score Breakdown
    score_res = client.get(f"/api/submissions/{req_id}/score")
    assert score_res.status_code == 200
    score_data = score_res.json()
    assert score_data["request_id"] == req_id
    assert score_data["score"] == 85
    assert score_data["decision"] == "GO"

    # Verify 7 criteria breakdown structure
    breakdown = score_data["breakdown"]
    expected_criteria = [
        "problem_clarity",
        "ai_solvability",
        "data_availability",
        "similar_projects",
        "research_needed",
        "technique_clarity",
        "integration",
    ]
    for criterion in expected_criteria:
        assert criterion in breakdown
        assert "score" in breakdown[criterion]
        assert "max" in breakdown[criterion]
