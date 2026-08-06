"""
tests/test_api_routes.py
Production Integration Tests for all FastAPI REST endpoints (`/api/*`).
"""

import pytest
from httpx import AsyncClient
from backend.models.db_schemes.requirementshub.schemes import Department


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient):
    """Test GET /api/health returns status ok."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy" or data.get("status") == "ok"


@pytest.mark.asyncio
async def test_departments_endpoints(async_client: AsyncClient, seeded_department: Department):
    """Test GET /api/departments/ listing and GET /api/departments/{id}."""
    # 1. List departments
    res_list = await async_client.get("/api/departments/")
    assert res_list.status_code == 200
    depts = res_list.json()
    assert isinstance(depts, list)
    assert len(depts) >= 1
    assert any(d["id"] == "corporate_support" for d in depts)

    # 2. Get department fields by ID
    res_single = await async_client.get("/api/departments/corporate_support/fields")
    assert res_single.status_code == 200
    dept_data = res_single.json()
    assert dept_data["id"] == "corporate_support"
    assert "Corporate & Support" in dept_data["display_name"]

    # 3. Get non-existent department returns 404
    res_404 = await async_client.get("/api/departments/non_existent_dept/fields")
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_submissions_crud_workflow(async_client: AsyncClient, sample_submission_payload: dict):
    """Test POST /api/submissions/ creation and GET retrieval workflow."""
    # 1. Create submission
    res_create = await async_client.post("/api/submissions/", json=sample_submission_payload)
    assert res_create.status_code == 201
    created_data = res_create.json()

    assert "request_id" in created_data
    request_id = created_data["request_id"]
    assert created_data["status"] == "PENDING"

    # 2. Fetch submission by ID
    res_get = await async_client.get(f"/api/submissions/{request_id}")
    assert res_get.status_code == 200
    get_data = res_get.json()
    assert get_data["request_id"] == request_id
    assert get_data["form_data"]["project_name"] == sample_submission_payload["project_name"]

    # 3. List submissions
    res_list = await async_client.get("/api/submissions/")
    assert res_list.status_code == 200
    items = res_list.json()
    assert isinstance(items, list)
    assert any(item["request_id"] == request_id for item in items)


@pytest.mark.asyncio
async def test_submission_not_found(async_client: AsyncClient):
    """Test GET /api/submissions/{request_id} for non-existent ID returns 404."""
    res = await async_client.get("/api/submissions/invalid_uuid_12345")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_pending_and_override_workflow(
    async_client: AsyncClient, sample_submission_payload: dict
):
    """Test AI Engineer Dashboard endpoints (listing pending requests and manual decision override)."""
    # 1. Create a submission
    res_create = await async_client.post("/api/submissions/", json=sample_submission_payload)
    assert res_create.status_code == 201
    request_id = res_create.json()["request_id"]

    # 2. Fetch dashboard pending items
    res_pending = await async_client.get("/api/dashboard/pending")
    assert res_pending.status_code == 200
    pending_items = res_pending.json()
    assert isinstance(pending_items, list)
    assert any(item["request_id"] == request_id for item in pending_items)

    # 3. Post manual decision override (GO)
    override_payload = {
        "decision": "GO",
        "reviewer_name": "Senior AI Engineer",
        "reviewer_notes": "Manually verified dataset feasibility and client readiness.",
    }
    res_override = await async_client.post(
        f"/api/dashboard/{request_id}/decision", json=override_payload
    )
    assert res_override.status_code == 200
    override_res = res_override.json()
    assert override_res["request_id"] == request_id
    assert override_res["decision"] == "GO"
    assert override_res["status"] == "COMPLETED"
    assert override_res["manual_override"] is True


@pytest.mark.asyncio
async def test_clarification_questions_endpoint(
    async_client: AsyncClient, sample_submission_payload: dict
):
    """Test GET /api/submissions/{request_id}/clarification."""
    res_create = await async_client.post("/api/submissions/", json=sample_submission_payload)
    assert res_create.status_code == 201
    request_id = res_create.json()["request_id"]

    res_clar = await async_client.get(f"/api/submissions/{request_id}/clarification")
    assert res_clar.status_code == 200
    clar_data = res_clar.json()
    assert clar_data["request_id"] == request_id
    assert "max_rounds" in clar_data
    assert "questions" in clar_data


@pytest.mark.asyncio
async def test_reports_endpoint_not_found(async_client: AsyncClient):
    """Test GET /api/reports/{request_id} returns 404 when report does not exist yet."""
    res = await async_client.get("/api/reports/non_existent_report_id")
    assert res.status_code == 404
