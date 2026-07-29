"""
Validate Completeness Node

Rule-based check: are all required fields present and non-empty?
Loads department config to know which fields are required.

Owner: Track B
"""

# TODO [Track B]: Implement validate_completeness node
#
# Input from state: form_data, department
# Output to state: missing_fields, is_complete
#
# def validate_completeness(state: PipelineState) -> dict:
#     1. Load department config from department_configs.json
#     2. Check all required_base_fields are present and non-empty
#     3. Check all required specific_fields are present
#     4. Return {"missing_fields": [...], "is_complete": len(missing) == 0}
