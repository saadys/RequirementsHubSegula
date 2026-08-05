"""
Tests for Core Submissions API Endpoints (Module B)
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_create_submission_success():
    """Test POST /api/submissions/ with valid corporate_support request (Asynchronous Background Tasks)."""
    payload = {
        "project_name": "AI Onboarding Assistant",
        "department": "corporate_support",
        "team_contact_name": "Jean Dupont",
        "team_contact_email": "jean.dupont@segula.fr",
        "problem_description": "New employees waste 2 weeks searching for internal HR and IT policies across static document folders.",
        "current_process": "Manual search on SharePoint and emailing colleagues.",
        "expected_outcome": "An intelligent conversational chatbot answering HR/IT questions instantly.",
        "data_description": "500 PDF policy documents and internal FAQ tables.",
        "deadline_urgency": "medium",
        "department_specific": {
            "service_area": "hr",
            "target_users": "all_employees",
            "has_existing_system": True,
        },
    }

    response = client.post("/api/submissions/", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "request_id" in data
    assert data["request_id"] is not None
    # Immediate response status is PENDING when using background tasks
    assert data["status"] == "PENDING"
    assert data["form_data"]["project_name"] == "AI Onboarding Assistant"

    # Test GET /api/submissions/{request_id} endpoint
    get_response = client.get(f"/api/submissions/{data['request_id']}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["request_id"] == data["request_id"]


def test_get_submission_by_id_and_list():
    """Test GET /api/submissions/{id} and GET /api/submissions/ listing."""
    payload = {
        "project_name": "Test Retrieval Project",
        "department": "corporate_support",
        "team_contact_name": "Alice Martin",
        "team_contact_email": "alice.martin@segula.fr",
        "problem_description": "Automated CV screening for specialized engineering roles to speed up candidate shortlisting.",
        "current_process": "Manual review of 200 CVs per week.",
        "expected_outcome": "Automated candidate scoring and ranking.",
        "deadline_urgency": "high",
        "department_specific": {
            "service_area": "hr",
            "target_users": "hr_team",
            "has_existing_system": False,
        },
    }

    create_res = client.post("/api/submissions/", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    req_id = created_data["request_id"]

    # Test GET by ID
    get_res = client.get(f"/api/submissions/{req_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["request_id"] == req_id
    assert get_data["form_data"]["project_name"] == "Test Retrieval Project"

    # Test List Submissions
    list_res = client.get("/api/submissions/?department=corporate_support")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert isinstance(list_data, list)
    matching = [s for s in list_data if s["request_id"] == req_id]
    assert len(matching) == 1


def test_get_submission_not_found():
    """Test GET /api/submissions/non_existent_id returns 404."""
    response = client.get("/api/submissions/non_existent_request_id_12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_submission_with_pdf_upload(tmp_path):
    """Test POST /api/submissions/upload with multipart form data and PDF attachment."""
    import json

    payload_dict = {
        "project_name": "PDF Processing Project",
        "department": "corporate_support",
        "team_contact_name": "Marc Petit",
        "team_contact_email": "marc.petit@segula.fr",
        "problem_description": "We need to extract requirements from PDF spec files and analyze them with AI.",
        "current_process": "Reading PDF documents manually.",
        "expected_outcome": "Automated PDF text extraction and AI feasibility analysis.",
        "deadline_urgency": "medium",
        "department_specific": {
            "service_area": "it",
            "target_users": "it_team",
            "has_existing_system": False,
        },
    }

    # Create dummy PDF file for testing
    pdf_file = tmp_path / "sample_spec.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 sample content for parsing test")

    with open(pdf_file, "rb") as f:
        files = {"file": ("sample_spec.pdf", f, "application/pdf")}
        data = {"form_data_json": json.dumps(payload_dict)}
        response = client.post("/api/submissions/upload", data=data, files=files)

    assert response.status_code == 201
    res_data = response.json()
    assert "request_id" in res_data
    assert res_data["status"] == "PENDING"

