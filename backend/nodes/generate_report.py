"""
Generate Report Node

Formats the final feasibility report (Cahier des Charges) in Markdown format
for requests that reach a GO or NO_GO decision, or a partial assessment report.

Owner: Track B / Shared Integration
"""

from backend.contracts.state import PipelineState


def generate_report(state: PipelineState) -> dict:
    """Generates a comprehensive Markdown feasibility report from graph state."""
    form_data = state.get("form_data", {}) or {}
    facts = state.get("extracted_facts", {}) or {}
    score = state.get("score", 0)
    breakdown = state.get("score_breakdown", {}) or {}
    decision = str(state.get("decision", "NO_GO")).upper()
    similar_projects = state.get("similar_projects", []) or []
    
    project_name = form_data.get("project_name", "AI Requirement Request")
    department = form_data.get("department", "Corporate & Support Services")
    contact_name = form_data.get("team_contact_name", "N/A")
    contact_email = form_data.get("team_contact_email", "N/A")

    # Decision Badge & Title
    if decision == "GO":
        status_badge = "🟢 **APPROVED (GO)** — Project meets technical and data feasibility criteria."
    elif decision == "NO_GO":
        status_badge = "🔴 **NOT RECOMMENDED (NO_GO)** — Significant feasibility gaps or unsuitable use case."
    else:
        status_badge = "🟡 **PARTIAL EVALUATION** — Needs further technical clarification."

    # Score breakdown table
    table_rows = []
    for criterion, data in breakdown.items():
        crit_name = criterion.replace("_", " ").title()
        if isinstance(data, dict):
            crit_score = data.get("score", 0)
            crit_max = data.get("max", 0)
        else:
            crit_score = data
            crit_max = "-"
        table_rows.append(f"| {crit_name} | {crit_score} / {crit_max} |")
    table_str = "\n".join(table_rows) if table_rows else "| Feasibility | N/A |"

    # Requirements list
    reqs = facts.get("extracted_requirements", [])
    if isinstance(reqs, list) and reqs:
        reqs_str = "\n".join(f"{i}. {r}" for i, r in enumerate(reqs, 1))
    else:
        reqs_str = "- No specific structured requirements extracted."

    # Risks list
    risks = facts.get("risks_identified", [])
    if isinstance(risks, list) and risks:
        risks_str = "\n".join(f"- ⚠️ {r}" for r in risks)
    else:
        risks_str = "- No major technical risks identified."

    # Similar projects list
    if similar_projects:
        similar_str_list = []
        for proj in similar_projects[:3]:
            p_name = proj.get("project_name", "Past Project")
            p_sol = proj.get("solution_description", "No summary")
            p_contact = proj.get("contact_person", "Segula AI Team")
            similar_str_list.append(f"- **{p_name}**: {p_sol} *(Contact: {p_contact})*")
        similar_str = "\n".join(similar_str_list)
    else:
        similar_str = "- No similar past projects found in ChromaDB."

    report_markdown = f"""# 📄 AI Project Feasibility Report: {project_name}

**Department:** {department}  
**Contact:** {contact_name} ({contact_email})  
**Overall Feasibility Score:** `{score}/100`  
**Decision Status:** {status_badge}

---

### 📊 Score Breakdown

| Criterion | Points |
| :--- | :--- |
{table_str}
| **Total Score** | **{score} / 100** |

---

### 💡 Executive Summary
{facts.get("summary", "No summary available.")}

---

### 🎯 Extracted Key Requirements
{reqs_str}

---

### 🛠️ Technical Assessment & Recommendation
- **Problem Category:** `{str(facts.get("problem_category", "unknown")).upper()}`
- **Recommended AI Technique:** `{facts.get("ai_technique_identified", "unknown")}`
- **Data Availability:** `{str(facts.get("data_availability", "unknown")).upper()}`
- **Integration Complexity:** `{str(facts.get("integration_complexity", "unknown")).title()}`
- **Estimated Development Effort:** `{str(facts.get("estimated_effort", "unknown")).title()}`

---

### 🔍 Reference Past Projects
{similar_str}

---

### ⚠️ Identified Risks & Recommendations
{risks_str}

---
*Report generated automatically by Segula AI Requirement Hub.*
"""

    report_type = "go" if decision == "GO" else ("no_go" if decision == "NO_GO" else "partial")

    return {
        "report": report_markdown,
        "report_type": report_type,
    }
