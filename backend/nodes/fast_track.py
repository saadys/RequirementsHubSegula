"""
Fast Track Node

Handles exact match cases — when RAG finds a project with >= 95% similarity.
Formats the response with existing solution info and contact person.

Owner: Track A
"""

from backend.contracts.state import PipelineState
from backend import config


def fast_track(state: PipelineState) -> dict:
    """Formats a fast-track report for requests that match an existing historic project."""
    project = state.get("exact_match_project", {}) or {}
    
    project_name = project.get("project_name", "Existing Solution")
    solution_desc = project.get("solution_description", "No detailed solution summary available.")
    contact_person = project.get("contact_person", "Segula AI Team")
    outcome = project.get("outcome", "Successful")
    
    match_pct = int(config.RAG_EXACT_MATCH_THRESHOLD * 100)
    
    ai_techniques = project.get("ai_techniques", [])
    if isinstance(ai_techniques, list):
        techniques_formatted = "\n".join(f"- {t}" for t in ai_techniques) if ai_techniques else "- General AI/ML"
    else:
        techniques_formatted = f"- {ai_techniques}"
        
    report_text = f"""# 🚀 Fast Track Evaluation: Existing Solution Identified

An existing AI solution matching your requirement with high confidence (>={match_pct}% similarity) has already been implemented within Segula Technologies.

### 📌 Project Details
- **Project Name:** {project_name}
- **Status / Outcome:** {outcome}
- **Contact Person:** {contact_person}

### 💡 Solution Summary
{solution_desc}

### 🛠️ AI Techniques Used
{techniques_formatted}

---
*Recommendation:* Rather than developing a new solution from scratch, please get in touch with **{contact_person}** to leverage or adapt the existing system.
"""

    return {
        "report": report_text,
        "report_type": "fast_track",
        "decision": "FAST_TRACK",
        "score": 95,
        "sub_scores": {
            "ai_viability": 30,
            "data_readiness": 25,
            "problem_clarity": 20,
            "integration_feasibility": 10,
            "governance_and_safety": 10,
        },
        "veto_triggered": False,
        "veto_reasons": [],
    }

