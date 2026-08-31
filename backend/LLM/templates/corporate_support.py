"""
Corporate & Support Services — Department Prompt Template

Specialized prompt template for Corporate & Support Services (HR, IT, Finance, Legal, Procurement, etc.).
"""

from typing import Any, Dict, List, Optional
from backend.LLM.templates.template import build_system_prompt


# ── Department-Specific Context ──────────────────────────────────

DEPARTMENT_CONTEXT = """## Department Context: Corporate & Support Services

You are analyzing a request submitted under the **Corporate & Support Services** department at Segula Technologies.

### 🚨 UNIVERSAL DEPARTMENT SCOPE RULE (PRIMARY END-USER CRITERION)
A project belongs to Corporate & Support Services ONLY IF the direct daily users of the AI tool are the internal administrative/support staff of Segula Technologies (e.g. in-house HR specialists, in-house accountants, corporate buyers, internal IT support agents, in-house legal counsel).

If the primary end-user is an operational professional, scientific researcher, field specialist, product designer, or external practitioner outside internal corporate management, the project is STRICTLY OUT-OF-SCOPE (`OUT_OF_SCOPE_OTHER` or `OUT_OF_SCOPE_ENGINEERING`), regardless of how viable or promising the AI technology is.

### The 10 In-Scope Core Functions:
1. **Human Resources (HR):** Employee lifecycle, personnel records, staffing movements, HR business partnering, employee relations.
2. **Recruitment & Talent Acquisition (TA):** Candidate sourcing, CV screening, job matching, internship pipelines, talent analytics.
3. **Finance & Controlling:** Accounting, invoice processing, line-item reconciliation, expense tracking, cost control, budget forecasting.
4. **Procurement / Achats:** Supplier management, vendor evaluation, purchase order processing, contract cost optimization.
5. **IT Internal Support & Infrastructure:** Tools used exclusively by internal corporate IT administrators for employee helpdesk ticketing, laptop/account provisioning, office network access, and internal corporate intranet portals.
   *(Note: The fact that a software application runs on a server, uses computing power, or processes digital files does NOT make it an IT Support project).*
6. **General Administration & Facilities:** Office management, workplace logistics, site administrative compliance.
7. **Legal & Compliance:** Tools used exclusively by in-house corporate legal counsel to draft, review, and negotiate business contracts, vendor NDAs, corporate governance policies, and legal disputes.
   *(Note: Merely having to comply with privacy laws, ethical standards, safety norms, or industry regulations does NOT make a project a Legal tool).*
8. **Quality & Process Compliance (Transversal):** Internal ISO standards, audit support, process optimization, deliverable quality checks.
9. **Training & Employee Onboarding:** Structured training programs, new hire onboarding paths, technical skills upskilling.
10. **Document Engineering & Knowledge Management:** Technical documentation, user manuals, repair guides, internal knowledge base indexing & retrieval.

### Department Scope Boundaries:
- **IN-SCOPE**: The project directly serves one of the 10 internal corporate support functions above where corporate staff are the primary users.
- **OUT-OF-SCOPE (ENGINEERING)**: The project is an operational engineering application (e.g. CAD, FEA structural stress simulation, CFD, crash testing, vehicle chassis dynamics, embedded software, manufacturing lines). 
  You MUST set `target_sub_function` to `OUT_OF_SCOPE_ENGINEERING`.
- **OUT-OF-SCOPE (OTHER)**: The project serves an operational, scientific, medical, clinical, or external business domain outside internal corporate administration.
  You MUST set `target_sub_function` to `OUT_OF_SCOPE_OTHER`."""


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
