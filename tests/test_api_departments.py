"""
Tests for Department Configuration API Endpoints (Phase 1)
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_list_departments():
    """Test GET /api/departments/ returns department list."""
    response = client.get("/api/departments/")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 5

    # Check corporate_support is present and enabled
    corp = next((d for d in data if d["id"] == "corporate_support"), None)
    assert corp is not None
    assert corp["display_name"] == "Corporate & Support Services"
    assert corp["enabled"] is True

    # Check disabled department
    sys_dev = next((d for d in data if d["id"] == "system_development"), None)
    assert sys_dev is not None
    assert sys_dev["enabled"] is False


def test_get_corporate_support_fields():
    """Test GET /api/departments/corporate_support/fields returns detailed field specs."""
    response = client.get("/api/departments/corporate_support/fields")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "corporate_support"
    assert data["display_name"] == "Corporate & Support Services"
    assert data["enabled"] is True
    assert len(data["specific_fields"]) == 4
    assert "project_name" in data["required_base_fields"]
    assert "team_contact_email" in data["required_base_fields"]

    # Verify a specific field structure
    service_area = next((f for f in data["specific_fields"] if f["name"] == "service_area"), None)
    assert service_area is not None
    assert service_area["type"] == "select"
    assert "hr" in service_area["options"]
    assert service_area["required"] is True


def test_get_non_existent_department_404():
    """Test GET /api/departments/invalid_dept/fields returns HTTP 404."""
    response = client.get("/api/departments/invalid_dept/fields")
    assert response.status_code == 404
    data = response.json()
    assert "Department 'invalid_dept' not found" in data["detail"]
