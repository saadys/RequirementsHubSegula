import pytest
from backend.nodes.validate_completeness import (
    validate_submission_fields,
    validate_completeness,
    is_value_empty,
)


def test_is_value_empty():
    assert is_value_empty(None) is True
    assert is_value_empty("") is True
    assert is_value_empty("   ") is True
    assert is_value_empty("valid text") is False
    assert is_value_empty(0) is False
    assert is_value_empty(False) is False


def test_validation_complete_payload():
    form_data = {
        "project_name": "AI Helpdesk Bot",
        "team_contact_name": "Jean Dupont",
        "team_contact_email": "jean.dupont@segula.fr",
        "problem_description": "High ticket resolution times in internal IT support",
        "current_process": "Manual ticketing system",
        "expected_outcome": "Automate level 1 ticket responses",
        "deadline_urgency": "medium",
        "department_specific": {
            "service_area": "it",
            "target_users": "employees",
            "has_existing_system": True,
        },
    }
    missing, is_complete = validate_submission_fields(form_data, "corporate_support")
    assert missing == []
    assert is_complete is True


def test_validation_missing_fields():
    form_data = {
        "project_name": "Incomplete Request",
        # Missing team_contact_name, email, problem_description, etc.
    }
    missing, is_complete = validate_submission_fields(form_data, "corporate_support")
    assert "team_contact_name" in missing
    assert "problem_description" in missing
    assert "department_specific.service_area" in missing
    assert is_complete is False


def test_validate_completeness_node():
    state = {
        "form_data": {
            "project_name": "Test Project",
            "team_contact_name": "Alice",
            "team_contact_email": "alice@test.com",
            "problem_description": "Problem desc",
            "current_process": "Process desc",
            "expected_outcome": "Outcome desc",
            "deadline_urgency": "high",
            "department_specific": {
                "service_area": "hr",
                "target_users": "managers",
                "has_existing_system": False,
            },
        },
        "department": "corporate_support",
    }
    update = validate_completeness(state)
    assert update["is_complete"] is True
    assert update["missing_fields"] == []
