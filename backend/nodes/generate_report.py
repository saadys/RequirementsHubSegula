"""
Generate Report Node

Formats the final executive feasibility dossier in Markdown format (Cahier des Charges)
with 5-pillar breakdown, circuit-breaker veto alerts, and recommended technical path.

Owner: Track B / Shared Integration
"""

from backend.contracts.state import PipelineState
from backend import config
import json
from backend.services.llm import get_llm


FEEDBACK_SYSTEM_PROMPT = (
    "We are at Segula Technologies, a global engineering and consulting group.\n"
    "A business team submitted an AI project request that evaluated to 'NO_GO' "
    "(rejected) or stalled in 'NEEDS_CLARIFICATION'. Your job is to provide constructive, "
    "actionable, and empathetic feedback so they know exactly *why* it was not approved "
    "and *exactly what steps* they can take to improve it (e.g., how to collect data, "
    "how to define a measurable KPI, or stating if they don't need AI at all).\n"
    "Be concise and professional. Format your response in clean Markdown (no top-level headings)."
)


def get_feedback_prompts(state: PipelineState) -> tuple[str, str]:
    """Builds the system and user prompts for AI Architect feedback."""
    score = state.get("score", 0)
    sub = state.get("sub_scores", {}) or {}
    veto = state.get("veto_reasons", []) or []
    decision = str(state.get("decision", "NO_GO")).upper()
    facts = state.get("extracted_facts", {}) or {}

    user_content = f"""
Decision: {decision}
Score: {score}/100
Sub-Scores: {json.dumps(sub)}
Veto Reasons: {json.dumps(veto)}
Project Summary: {facts.get('project_summary', 'N/A')}

Provide 1-2 paragraphs of actionable advice. Be precise about what they must fix (Data, Scope, Integration) for the next submission.
"""
    return FEEDBACK_SYSTEM_PROMPT, user_content


def _generate_ai_feedback(decision: str, score: int, sub: dict, veto: list, facts: dict) -> str:
    """Uses the LLM to generate dynamic, actionable feedback for rejected or stalled projects."""
    llm = get_llm()
    state = {
        "score": score,
        "sub_scores": sub,
        "veto_reasons": veto,
        "decision": decision,
        "extracted_facts": facts,
    }
    system_prompt, user_content = get_feedback_prompts(state)
    try:
        return llm.generate_text(
            prompt=user_content,
            system_prompt=system_prompt,
            temperature=0.7
        ).strip()
    except Exception as e:
        import logging
        logging.getLogger("backend.nodes.generate_report").error(f"Feedback generation failed: {e}")
        return "Please review the 5-pillar breakdown and veto alerts above to address the bottlenecks in your project data or scope."


def build_static_report_markdown(state: PipelineState) -> str:
    """Builds the structured 5-pillar Markdown feasibility dossier header."""
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

    if best_proj and max_rag >= getattr(config, "RAG_SIMILAR_THRESHOLD", 0.60):
        proj_info = f"- **Parent Project Match:** {best_proj.get('project_name')} (Similarity: {max_rag*100:.1f}%)"
    else:
        proj_info = f"- **RAG Similarity:** {max_rag*100:.1f}% (Novel Project)"

    identified_technique = (
        facts.get("identified_technique")
        or facts.get("ai_technique_identified")
        or "Standard Python script or technical review"
    )
    summary_text = facts.get("project_summary") or facts.get("summary", "No summary available.")

    return f"""# 📋 AI Project Feasibility Dossier: {project_name}

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


def generate_report(state: PipelineState) -> dict:
    """Generates a comprehensive Markdown feasibility dossier from graph state."""
    facts = state.get("extracted_facts", {}) or {}
    score = state.get("score", 0)
    sub = state.get("sub_scores", {}) or {}
    veto = state.get("veto_reasons", []) or []
    decision = str(state.get("decision", "NO_GO")).upper()

    report_markdown = build_static_report_markdown(state)

    if decision in ["NO_GO", "NEEDS_CLARIFICATION"]:
        feedback_text = _generate_ai_feedback(decision, score, sub, veto, facts)
        report_markdown += f"\n---\n\n### 🧠 AI Architect Feedback & Actionable Next Steps:\n{feedback_text}\n"

    report_type = "go" if decision in ["GO", "FAST_TRACK"] else ("no_go" if decision == "NO_GO" else "partial")

    return {
        "report": report_markdown,
        "report_type": report_type,
    }

