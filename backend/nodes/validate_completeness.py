"""
Node: validate_completeness
Responsibility: Validate submitted form data against required base fields 
and department-specific field rules loaded from department_configs.json.
"""

import json
import logging
from pathlib import Path
from typing import Any

from backend.contracts.state import PipelineState

logger = logging.getLogger(__name__)

# Default path to department configurations
CONFIG_FILE_PATH = Path(__file__).resolve().parent.parent / "data" / "department_configs.json"

DEFAULT_BASE_FIELDS = [
    "project_name",
    "team_contact_name",
    "team_contact_email",
    "problem_description",
    "current_process",
    "expected_outcome",
    "deadline_urgency",
]


def load_department_configs(config_path: Path | None = None) -> dict[str, Any]:
    """
    Load department configuration rules from JSON file.
    """
    target_path = config_path or CONFIG_FILE_PATH
    if not target_path.exists():
        logger.error("Department configuration file not found at: %s", target_path)
        return {}

    try:
        with open(target_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as exc:
        logger.error("Error reading department configs at %s: %s", target_path, exc)
        return {}


def is_value_empty(val: Any) -> bool:
    """
    Check if a field value is None, empty string, or whitespace only.
    """
    if val is None:
        return True
    if isinstance(val, str) and not val.strip():
        return True
    return False


def validate_submission_fields(
    form_data: dict[str, Any],
    department: str,
    config_path: Path | None = None,
) -> tuple[list[str], bool]:
    """
    Validate form fields against base rules and department-specific config.

    Args:
        form_data (dict): Form payload dictionary.
        department (str): Key of target department (e.g., 'corporate_support').
        config_path (Path | None): Custom path for department_configs.json.

    Returns:
        tuple[list[str], bool]: List of missing field names and boolean completeness flag.
    """
    form_data = form_data or {}
    configs = load_department_configs(config_path)
    dept_config = configs.get(department, {})

    missing_fields: list[str] = []

    # 1. Validate Base Fields
    required_base = dept_config.get("required_base_fields", DEFAULT_BASE_FIELDS)
    for field_name in required_base:
        val = form_data.get(field_name)
        if is_value_empty(val):
            missing_fields.append(field_name)

    # 2. Validate Department-Specific Fields
    dept_specific_data = form_data.get("department_specific", {})
    specific_fields_rules = dept_config.get("specific_fields", [])

    for field_rule in specific_fields_rules:
        field_name = field_rule.get("name")
        is_required = field_rule.get("required", False)

        if is_required and field_name:
            # Look in department_specific dict first, then top-level form_data
            val = dept_specific_data.get(field_name, form_data.get(field_name))
            if is_value_empty(val):
                missing_fields.append(f"department_specific.{field_name}")

    is_complete = len(missing_fields) == 0
    return missing_fields, is_complete


def validate_completeness(state: PipelineState) -> dict[str, Any]:
    """
    LangGraph Node function for completeness validation.

    Args:
        state (PipelineState): Current graph state containing 'form_data' and 'department'.

    Returns:
        dict: State update dictionary containing 'missing_fields' and 'is_complete'.
    """
    form_data = state.get("form_data", {})
    department = state.get("department", "")

    missing_fields, is_complete = validate_submission_fields(form_data, department)

    logger.info(
        "Validation completed for department '%s' | complete=%s missing_fields_count=%d",
        department,
        is_complete,
        len(missing_fields),
    )

    return {
        "missing_fields": missing_fields,
        "is_complete": is_complete,
    }
