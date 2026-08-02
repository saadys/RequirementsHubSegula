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
    """Test fetching report and score breakdown for a complete GO submission."""
    payload = {
        "project_name": "AI Document Archival Classifier",
        "department": "corporate_support",
        "team_contact_name": "Marc Petit",
        "team_contact_email": "marc.petit@segula.fr",
        "problem_description": "HR and IT document archives are unstructured, making audit compliance difficult.",
        "current_process": "Manual document labeling and filing into nested shared drives.",
        "expected_outcome": "Automated NLP classification tagging all uploaded archives into structured folders.",
        "data_description": "10,000 labeled PDF documents and taxonomy dictionary.",
        "deadline_urgency": "high",
        "department_specific": {
            "service_area": "it",
            "target_users": "it_team",
            "has_existing_system": True,
        },
    }

    create_res = client.post("/api/submissions/", json=payload)
    assert create_res.status_code == 201
    submission = create_res.json()
    req_id = submission["request_id"]

    # 1. Fetch Report
    report_res = client.get(f"/api/submissions/{req_id}/report")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["request_id"] == req_id
    assert report_data["is_available"] is True
    assert report_data["report_type"] in ["go", "cahier_des_charges", "FULL_CAHIER_DES_CHARGES", "FAST_TRACK_SOLUTION"]
    assert len(report_data["report"]) > 100

    # 2. Fetch Score Breakdown
    score_res = client.get(f"/api/submissions/{req_id}/score")
    assert score_res.status_code == 200
    score_data = score_res.json()
    assert score_data["request_id"] == req_id
    assert score_data["score"] >= 70
    assert score_data["decision"] == "GO"
    assert score_data["percentage"] == score_data["score"]

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
