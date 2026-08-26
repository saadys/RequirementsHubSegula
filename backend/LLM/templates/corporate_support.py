"""
Corporate & Support Services — Department Prompt Template

Specialized prompt template for Corporate & Support Services (HR, IT, Finance, Legal, Procurement, etc.).
"""

from typing import Any, Dict, List, Optional
from backend.LLM.templates.template import build_system_prompt


# ── Department-Specific Context ──────────────────────────────────

DEPARTMENT_CONTEXT = """## Department Context: Corporate & Support Services

You are analyzing a request submitted under the **Corporate & Support Services** department at Segula Technologies (Casablanca Nearshore & Global Delivery Hubs).

### The 11 In-Scope Core Functions:
1. **Human Resources (HR):** Employee lifecycle, personnel records, staffing movements, HR business partnering, employee relations.
2. **Recruitment & Talent Acquisition (TA):** Candidate sourcing, CV screening, job matching, internship pipelines, talent analytics.
3. **Finance & Controlling:** Accounting, invoice processing, line-item reconciliation, expense tracking, cost control, budget forecasting.
4. **Procurement / Achats:** Supplier management, vendor evaluation, purchase order processing, contract cost optimization.
5. **IT Support & Infrastructure:** Internal helpdesk ticketing, network/systems management, IT asset tracking, internal developer tools & portals.
6. **General Administration & Facilities:** Office management, workplace logistics, site administrative compliance.
7. **Legal & Compliance:** Contract review, legal risk analysis, intellectual property, regulatory compliance, GDPR privacy.
8. **Corporate Communication:** Internal communications, employer branding, CSR initiatives, change management.
9. **Quality & Process Compliance (Transversal):** Internal ISO standards, audit support, process optimization, deliverable quality checks.
10. **Training & Employee Onboarding:** Structured training programs, new hire onboarding paths, technical skills upskilling.
11. **Document Engineering & Knowledge Management:** Technical documentation, user manuals, repair guides, internal knowledge base indexing & retrieval.

### Department Scope Boundaries:
- **RELEVANT**: The project directly serves one of the 11 functions above.
- **PARTIALLY_RELEVANT**: The project is initiated by a Corporate Support team (e.g., HR, Finance, Procurement) but handles technical/engineering domain data (e.g., HR screening mechanical engineering CVs, Procurement processing automotive part invoices).
- **UNRELATED**: The project is purely an operational engineering, manufacturing, automotive design, mechatronics, embedded systems, crash simulation, medical/pharma/healthcare, or other external domain that does not belong to Corporate & Support Services. Mark `department_relevance` as `UNRELATED`.

### Common AI Opportunities in This Department
- **Document intelligence:** Searching, summarizing, and answering questions from large internal document repositories (HR policies, IT wikis, legal contracts, invoices).
- **Process automation:** Automating repetitive administrative tasks (ticket routing, form processing, reconciliation, data entry).
- **Employee-facing assistants:** Chatbots and virtual assistants that help employees find information, complete onboarding, or troubleshoot IT issues.
- **Recruitment & talent analytics:** CV screening, candidate matching, skills assessment, bias detection in hiring pipelines.
- **Predictive analytics:** Employee attrition prediction, IT incident forecasting, budget anomaly detection.

### Typical Data Sources
- Internal documents (PDF, Word, SharePoint, Confluence)
- HR information systems (HRIS), employee records
- IT ticketing systems (Jira, ServiceNow)
- Email and communication logs
- Applicant Tracking Systems (ATS), CVs, job descriptions
- ERP and accounting tables (SAP, invoices, purchase orders)

### Department-Specific Risks to Watch For
- **Data privacy / GDPR:** Employee personal data, candidate information, and HR records are highly sensitive. Any AI solution MUST consider data protection regulations.
- **Bias and fairness:** Recruitment and HR analytics carry significant risk of algorithmic bias. Flag this for any project involving employee evaluation or candidate selection.
- **User adoption:** Internal tools often face resistance from non-technical users. Consider whether the proposed solution accounts for user experience and change management.
- **Integration with legacy systems:** Many corporate tools (SAP, legacy HRIS, old SharePoint) have limited API access. Flag integration complexity honestly.
- **Multilingual requirements:** Segula operates internationally — solutions may need to handle French, English, and other languages."""


# ── Public API ───────────────────────────────────────────────────

def get_prompt(
    form_data: dict,
    similar_projects: Optional[List[Dict[str, Any]]] = None,
    clarification_round: int = 0,
    clarification_answers: Optional[List[str]] = None,
    clarification_questions: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """Builds the full message list for Corporate & Support Services department."""

    system_prompt = build_system_prompt(
        department_context=DEPARTMENT_CONTEXT,
        similar_projects=similar_projects,
        clarification_round=clarification_round,
        clarification_answers=clarification_answers,
        clarification_questions=clarification_questions,
    )

    user_parts = ["# AI Project Request\n"]

    if form_data.get("project_name"):
        user_parts.append(f"**Project Name:** {form_data["project_name"]}")
    if form_data.get("department"):
        user_parts.append(f"**Department:** {form_data["department"]}")
    if form_data.get("problem_description"):
        user_parts.append(f"\n## Problem Description\n{form_data["problem_description"]}")
    if form_data.get("current_process"):
        user_parts.append(f"\n## Current Process\n{form_data["current_process"]}")
    if form_data.get("expected_outcome"):
        user_parts.append(f"\n## Expected Outcome\n{form_data["expected_outcome"]}")
    if form_data.get("data_description"):
        user_parts.append(f"\n## Available Data\n{form_data["data_description"]}")
    if form_data.get("deadline_urgency"):
        user_parts.append(f"\n**Deadline Urgency:** {form_data["deadline_urgency"]}")

    user_message = "\n".join(user_parts)

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
