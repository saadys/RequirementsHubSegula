"""
Generate Report Node

Formats the final executive feasibility dossier in Markdown format (Cahier des Charges)
with 5-pillar breakdown, circuit-breaker veto alerts, and recommended technical path.

Owner: Track B / Shared Integration
"""

from backend.contracts.state import PipelineState
from backend import config


def generate_report(state: PipelineState) -> dict:
    """Generates a comprehensive Markdown feasibility dossier from graph state."""
    form_data = state.get("form_data", {}) or {}
    facts = state.get("extracted_facts", {}) or {}
    score = state.get("score", 0)
    sub = state.get("sub_scores", {}) or {}
    veto = state.get("veto_reasons", []) or []
    decision = str(state.get("decision", "NO_GO")).upper()
    rag_scores = state.get("rag_scores", [])
    max_rag = max(rag_scores) if rag_scores else 0.0
    similar_projects = state.get("similar_projects", []) or []
    best_proj = similar_projects[0] if similar_projects else None
    round_num = state.get("clarification_round", 0)
    max_rounds = getattr(config, "MAX_CLARIFICATION_ROUNDS", 2)

    project_name = form_data.get("project_name", "AI Requirement Request")
    department = form_data.get("department", "Corporate & Support Services")
    contact_name = form_data.get("team_contact_name", "N/A")
    contact_email = form_data.get("team_contact_email", "N/A")

    # Safe extraction of pillar categories and reasons
    def _get_cat_and_reason(pillar_key: str) -> tuple[str, str]:
        obj = facts.get(pillar_key)
        if isinstance(obj, dict):
            return obj.get("category", "N/A"), obj.get("reason", "N/A")
        return facts.get(f"{pillar_key}_category", "N/A"), facts.get(f"{pillar_key}_reason", "N/A")

    ai_cat, ai_reason = _get_cat_and_reason("ai_viability")
    data_cat, data_reason = _get_cat_and_reason("data_readiness")
    clarity_cat, clarity_reason = _get_cat_and_reason("problem_clarity")
    integ_cat, integ_reason = _get_cat_and_reason("integration_feasibility")
    if integ_cat == "N/A":
        integ_cat, integ_reason = _get_cat_and_reason("integration")
    gov_cat, gov_reason = _get_cat_and_reason("governance_and_safety")
    if gov_cat == "N/A":
        gov_cat, gov_reason = _get_cat_and_reason("governance")

    # Parent project matching / RAG similarity indicator
    if best_proj and max_rag >= getattr(config, "RAG_SIMILAR_THRESHOLD", 0.60):
        proj_info = f"- **Parent Project Match:** {best_proj.get('project_name')} (Similarity: {max_rag*100:.1f}%)"
    else:
        proj_info = f"- **RAG Similarity:** {max_rag*100:.1f}% (Novel Project)"

    # Recommended technical path
    identified_technique = (
        facts.get("identified_technique")
        or facts.get("ai_technique_identified")
        or "Standard Python script or technical review"
    )
    summary_text = facts.get("project_summary") or facts.get("summary", "No summary available.")

    report_markdown = f"""# 📋 AI Project Feasibility Dossier: {project_name}

**Department:** {department}  
**Contact:** {contact_name} ({contact_email})  

## 🎯 Executive Verdict: **{decision}** (Feasibility Score: **{score}/100**)
- **Clarification Round:** {round_num} / {max_rounds}
{proj_info}

---

### 💡 Executive Summary
{summary_text}

---

### 📊 5-Pillar Rubric Breakdown:
1. **AI Technical Viability:** `{ai_cat}` ({sub.get('ai_viability', 0)}/30 pts)
   - *Rationale:* {ai_reason}
2. **Data Readiness & Labels:** `{data_cat}` ({sub.get('data_readiness', 0)}/25 pts)
   - *Rationale:* {data_reason}
3. **Problem Scope & Clarity:** `{clarity_cat}` ({sub.get('problem_clarity', 0)}/20 pts)
   - *Rationale:* {clarity_reason}
4. **Integration Feasibility:** `{integ_cat}` ({sub.get('integration', 0)}/15 pts)
   - *Rationale:* {integ_reason}
5. **Governance & Ethics:** `{gov_cat}` ({sub.get('governance', 0)}/10 pts)
   - *Rationale:* {gov_reason}

---

### 🚨 Veto & Risk Alerts:
{chr(10).join(f"- ⚠️ {r}" for r in veto) if veto else "✅ No critical veto flags encountered."}

---

### 💡 Recommended Next Steps:
- **Technical Path:** {identified_technique}
"""

    report_type = "go" if decision in ["GO", "FAST_TRACK"] else ("no_go" if decision == "NO_GO" else "partial")

    return {
        "report": report_markdown,
        "report_type": report_type,
    }

