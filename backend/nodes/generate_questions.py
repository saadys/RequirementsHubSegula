"""
Generate Questions Node

When feasibility score indicates clarification is required (e.g. 20-69),
generates dynamic, targeted clarification questions based on weak pillars
and identified blockers in the extracted facts.
"""

import json
from backend.contracts.state import PipelineState
from backend.schemas import ClarificationQuestionsModel
from backend.services.llm import get_clarification_llm


def generate_questions(state: PipelineState) -> dict:
    """Node that generates targeted clarification questions based on weak pillars and gaps."""
    facts = state.get("extracted_facts", {}) or {}
    sub_scores = state.get("sub_scores", {})
    veto_reasons = state.get("veto_reasons", [])
    current_round = state.get("clarification_round", 0)

    # 1. Identify specific gaps or uncertainties across the 5 pillars
    gaps = []
    
    # Check 5-pillar facts
    ai_viability = facts.get("ai_viability") if isinstance(facts.get("ai_viability"), dict) else {}
    data_readiness = facts.get("data_readiness") if isinstance(facts.get("data_readiness"), dict) else {}
    problem_clarity = facts.get("problem_clarity") if isinstance(facts.get("problem_clarity"), dict) else {}
    integration = facts.get("integration_feasibility") if isinstance(facts.get("integration_feasibility"), dict) else {}
    governance = facts.get("governance_and_safety") if isinstance(facts.get("governance_and_safety"), dict) else {}

    if data_readiness.get("category") in ["NONE", "UNLABELED_OR_MESSY"]:
        gaps.append(f"Data Readiness ({data_readiness.get('category')}): {data_readiness.get('reason', 'Missing clear volume, format, or label access.')}")

    if problem_clarity.get("category") in ["VAGUE", "PARTIAL", "CONTRADICTORY"]:
        gaps.append(f"Problem Clarity ({problem_clarity.get('category')}): {problem_clarity.get('reason', 'Missing concrete KPI, volume, or defined process boundaries.')}")

    if integration.get("category") == "COMPLEX":
        gaps.append(f"Integration Feasibility (COMPLEX): {integration.get('reason', 'Complex legacy or real-time infrastructure dependencies.')}")

    if governance.get("category") in ["MODERATE_RISK", "CRITICAL_RISK"]:
        gaps.append(f"Governance & Ethics ({governance.get('category')}): {governance.get('reason', 'Sensitive data or compliance boundary needed.')}")

    if not gaps and veto_reasons:
        gaps.extend(veto_reasons)

    # 2. Build prompt for the clarification LLM
    system_prompt = (
        "You are a Senior AI Requirements Engineer at Segula Technologies.\n"
        "An internal business team submitted an AI project request, but the feasibility evaluation "
        "requires targeted clarification. Your task is to generate 2 to 3 precise, polite, and actionable "
        "clarification questions to resolve the data, scope, or integration ambiguities."
    )

    gaps_text = "\n".join(f"- {gap}" for gap in gaps) if gaps else "- Requirement scope or data volume details are incomplete."
    summary_text = facts.get("project_summary") or facts.get("summary", "No summary available.")
    
    user_content = f"""The project requires clarification before a final feasibility decision can be made.
Project Summary: {summary_text}
Sub-Scores: {json.dumps(sub_scores)}
Identified Gaps / Blockers:
{gaps_text}

Generate 2-3 precise questions targeted at resolving the data, scope, or clarity ambiguities."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    # 3. Call structured LLM for clarification questions
    llm = get_clarification_llm()
    result: ClarificationQuestionsModel = llm.generate_structured_output(
        prompt=messages,
        response_schema=ClarificationQuestionsModel,
    )

    questions_payload = [q.model_dump() for q in result.questions]

    return {
        "clarification_questions": questions_payload,
        "clarification_round": current_round + 1,
    }

