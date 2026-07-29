"""
Generate Report Node

Builds the final "cahier de charge" document from a markdown template.
Handles three report types: go, no_go, partial (with uncertainty flags).

Owner: Track B
"""

# TODO [Track B]: Implement generate_report node
#
# Input from state: form_data, extracted_facts, score, score_breakdown,
#                   decision, similar_projects, report_type
# Output to state: report (markdown string)
#
# Report template sections:
#   - Project Overview (name, department, contact, score)
#   - Score Breakdown (table of criteria)
#   - Problem Statement (from extracted_facts.summary)
#   - Extracted Requirements (numbered list)
#   - Similar Past Projects (from RAG)
#   - Identified Risks
#   - Recommended AI Approach
#   - Uncertainties / Flags (for partial reports)
