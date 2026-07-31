"""
Corporate & Support Services — Department Prompt

System prompt specialized for the Corporate & Support Services department.
Covers: HR, IT, Internal Tools, Recruitment, Onboarding, Knowledge Management.

Owner: Track A
"""

from backend.prompts.base import build_system_prompt


# ── Department-Specific Context ──────────────────────────────────

DEPARTMENT_CONTEXT = """## Department Context: Corporate & Support Services

You are analyzing a request from the **Corporate & Support Services** department at Segula Technologies. This department encompasses:

- **Human Resources (HR):** Recruitment, onboarding, employee self-service, policy management, talent assessment.
- **IT / Internal Tools:** Helpdesk automation, knowledge base systems, IT asset management, internal developer tools.
- **Legal & Compliance:** Document review, contract analysis, regulatory compliance tracking.
- **Finance & Administration:** Invoice processing, expense management, budget forecasting.
- **Communication & Training:** Internal communication platforms, e-learning, employee engagement.

### Common AI Opportunities in This Department
- **Document intelligence:** Searching, summarizing, and answering questions from large internal document repositories (HR policies, IT wikis, legal contracts).
- **Process automation:** Automating repetitive administrative tasks (ticket routing, form processing, data entry).
- **Employee-facing assistants:** Chatbots and virtual assistants that help employees find information, complete onboarding, or troubleshoot IT issues.
- **Recruitment & talent analytics:** CV screening, candidate matching, skills assessment, bias detection in hiring pipelines.
- **Predictive analytics:** Employee attrition prediction, IT incident forecasting, budget anomaly detection.

### Typical Data Sources
- Internal documents (PDF, Word, SharePoint, Confluence)
- HR information systems (HRIS), employee records
- IT ticketing systems (Jira, ServiceNow)
- Email and communication logs
- Applicant Tracking Systems (ATS), CVs, job descriptions

### Department-Specific Risks to Watch For
- **Data privacy / GDPR:** Employee personal data, candidate information, and HR records are highly sensitive. Any AI solution MUST consider data protection regulations.
- **Bias and fairness:** Recruitment and HR analytics carry significant risk of algorithmic bias. Flag this for any project involving employee evaluation or candidate selection.
- **User adoption:** Internal tools often face resistance from non-technical users. Consider whether the proposed solution accounts for user experience and change management.
- **Integration with legacy systems:** Many corporate tools (SAP, legacy HRIS, old SharePoint) have limited API access. Flag integration complexity honestly.
- **Multilingual requirements:** Segula operates internationally — solutions may need to handle French, English, and other languages."""


# ── Public API ───────────────────────────────────────────────────

def get_prompt(
    form_data: dict,
    similar_projects: list[dict] | None = None,
    clarification_round: int = 0,
    clarification_answers: list[str] | None = None,
    clarification_questions: list[str] | None = None,
) -> list[dict]:
    """Builds the full message list for the Corporate & Support Services department.
    
    Returns a list of message dicts ready for LLM invocation:
    [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
    """
    
    # Build the system prompt (base + department context + RAG + clarification)
    system_prompt = build_system_prompt(
        department_context=DEPARTMENT_CONTEXT,
        similar_projects=similar_projects,
        clarification_round=clarification_round,
        clarification_answers=clarification_answers,
        clarification_questions=clarification_questions,
    )
    
    # Build the user message from form data
    user_parts = ["# AI Project Request\n"]
    
    if form_data.get("project_name"):
        user_parts.append(f"**Project Name:** {form_data['project_name']}")
    if form_data.get("department"):
        user_parts.append(f"**Department:** {form_data['department']}")
    if form_data.get("problem_description"):
        user_parts.append(f"\n## Problem Description\n{form_data['problem_description']}")
    if form_data.get("current_process"):
        user_parts.append(f"\n## Current Process\n{form_data['current_process']}")
    if form_data.get("expected_outcome"):
        user_parts.append(f"\n## Expected Outcome\n{form_data['expected_outcome']}")
    if form_data.get("data_description"):
        user_parts.append(f"\n## Available Data\n{form_data['data_description']}")
    if form_data.get("deadline_urgency"):
        user_parts.append(f"\n**Deadline Urgency:** {form_data['deadline_urgency']}")
    
    user_message = "\n".join(user_parts)
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
