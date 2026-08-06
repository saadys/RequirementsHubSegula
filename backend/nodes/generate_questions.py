"""
Generate Questions Node

When feasibility score is 40-69 (NEEDS_CLARIFICATION), generates targeted
clarification questions based on gaps identified in the extracted facts.

Owner: Track A
"""

from backend.contracts.state import PipelineState
from backend.schemas import ClarificationQuestions
from backend.services.llm import get_clarification_llm


def generate_questions(state: PipelineState) -> dict:
    """Node that generates targeted clarification questions based on uncertain fields."""
    facts = state.get("extracted_facts", {}) or {}
    current_round = state.get("clarification_round", 0)
    
    # 1. Identify specific gaps or uncertainties in extracted facts
    gaps = []
    
    if not facts.get("has_clear_problem_statement", True):
        gaps.append("Problem description is unclear or lacks specific business pain points.")
        
    if not facts.get("problem_is_ai_solvable", True):
        gaps.append("It is uncertain if the described problem can be realistically solved using AI/ML.")
        
    if facts.get("problem_category") == "unknown":
        gaps.append("The AI problem category (e.g. NLP, Computer Vision, Classification) could not be determined.")
        
    if facts.get("data_availability") in ["none", "partial"]:
        gaps.append(f"Data availability is rated as '{facts.get('data_availability')}'. Details on data sources, format, or access are missing.")
        
    if facts.get("data_volume_sufficient") in ["no", "unknown"]:
        gaps.append(f"Data volume sufficiency is rated as '{facts.get('data_volume_sufficient')}'. Exact volume estimates (e.g. rows, documents, images) are unspecified.")
        
    if facts.get("ai_technique_identified") == "unknown":
        gaps.append("A specific AI technique could not be identified due to missing technical requirements.")

    # 2. Build prompt for the clarification LLM
    system_prompt = (
        "You are a Senior AI Systems Analyst at Segula Technologies.\n"
        "An internal business team submitted an AI project request, but our initial feasibility evaluation "
        "identified critical gaps or uncertainties. Your task is to generate up to 5 targeted, concise, and polite "
        "clarification questions for the team so we can complete an accurate feasibility assessment.\n\n"
        "Guidelines:\n"
        "1. Direct each question at a specific missing detail (data size/format, current manual process, system integration, etc.).\n"
        "2. Keep questions easy to understand for business users.\n"
        "3. Provide a brief technical reasoning for why each question is necessary."
    )
    
    gaps_text = "\n".join(f"- {gap}" for gap in gaps) if gaps else "- General requirement details are incomplete."
    summary_text = facts.get("summary", "No summary available.")
    
    user_content = (
        f"### Request Summary:\n{summary_text}\n\n"
        f"### Identified Gaps & Uncertainties:\n{gaps_text}"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    
    # 3. Call structured LLM for clarification questions
    llm = get_clarification_llm()
    result: ClarificationQuestions = llm.invoke(messages)
    
    return {
        "clarification_questions": result.questions,
        "clarification_round": current_round + 1,
    }
