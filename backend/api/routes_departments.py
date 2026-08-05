"""
Department Configuration API Routes

Provides department list and field definitions for dynamic forms.
"""

import json
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from backend.config import DEPARTMENT_CONFIGS_PATH
from backend.schemas import DepartmentDetail, DepartmentSummary, SpecificField

router = APIRouter(prefix="/departments", tags=["Departments"])


def _load_department_configs() -> Dict[str, Any]:
    try:
        with open(DEPARTMENT_CONFIGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load department configs: {str(e)}",
        )


@router.get("/", response_model=List[DepartmentSummary], summary="List all departments")
async def list_departments():
    """Returns list of departments with display names and enabled status."""
    configs = _load_department_configs()
    departments = []
    for dept_id, data in configs.items():
        departments.append(
            DepartmentSummary(
                id=dept_id,
                display_name=data.get("display_name", dept_id),
                description=data.get("description", ""),
                enabled=data.get("enabled", False),
            )
        )
    return departments


@router.get(
    "/{dept_id}/fields",
    response_model=DepartmentDetail,
    summary="Get department form fields and rules",
)
async def get_department_fields(dept_id: str):
    """Returns detailed form fields and validation requirements for a department."""
    configs = _load_department_configs()
    if dept_id not in configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department '{dept_id}' not found",
        )

    dept_data = configs[dept_id]
    return DepartmentDetail(
        id=dept_id,
        display_name=dept_data.get("display_name", dept_id),
        description=dept_data.get("description", ""),
        enabled=dept_data.get("enabled", False),
        specific_fields=dept_data.get("specific_fields", []),
        required_base_fields=dept_data.get("required_base_fields", []),
    )
