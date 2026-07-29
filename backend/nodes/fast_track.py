"""
Fast Track Node

Handles exact match cases — when RAG finds a project with >= 95% similarity.
Formats the response with existing solution info and contact person.

Owner: Track A
"""

# TODO [Track A]: Implement fast_track node
#
# Input from state: exact_match_project
# Output to state: report, report_type="fast_track"
#
# def fast_track(state: PipelineState) -> dict:
#     1. Extract project details from exact_match_project
#     2. Format a report: "This solution already exists: [name]"
#     3. Include: solution summary, contact person, project outcome
#     4. Return {"report": formatted_report, "report_type": "fast_track"}
