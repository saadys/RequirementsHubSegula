"""
LLM Analyze Node

Calls the LLM with structured output to extract FactExtraction from the
business team's request. Uses department-specific prompts and RAG context.

Owner: Track A
"""

from backend.contracts.state import PipelineState
from backend.schemas import FactExtraction
from backend.services.llm import get_structured_llm
from backend import config
from backend.prompts.corporate_support import get_prompt as get_corporate_support_prompt


def llm_analyze(state: PipelineState) -> dict:
    """Node that invokes the structured LLM to extract facts from the request."""
    form_data = state.get("form_data", {}).copy()
    parsed_files = state.get("parsed_files_text", [])
    
    # Append parsed file content to problem description if available
    if parsed_files:
        files_text = "\n\n### Uploaded File Attachments:\n" + "\n---\n".join(parsed_files)
        existing_problem = form_data.get("problem_description", "")
        form_data["problem_description"] = f"{existing_problem}\n{files_text}".strip()

    # Filter RAG results by similarity threshold (e.g. >= 0.60) before injecting into prompt
    similar_projects = state.get("similar_projects", [])
    rag_scores = state.get("rag_scores", [])
    similarity_threshold = getattr(config, "RAG_SIMILAR_THRESHOLD", 0.60)
    
    filtered_projects = [
        proj for proj, score in zip(similar_projects, rag_scores)
        if score >= similarity_threshold
    ]
    
    # Get clarification parameters if any
    clarification_round = state.get("clarification_round", 0)
    clarification_answers = state.get("clarification_answers", [])
    clarification_questions = state.get("clarification_questions", [])

    # Select prompt builder based on department (defaulting to corporate_support)
    prompt_builder = get_corporate_support_prompt

    # Build messages for LLM invocation
    messages = prompt_builder(
        form_data=form_data,
        similar_projects=filtered_projects if filtered_projects else None,
        clarification_round=clarification_round,
        clarification_answers=clarification_answers,
        clarification_questions=clarification_questions,
    )

    # Invoke LLM provider with structured output schema (FactExtraction)
    llm = get_structured_llm()
    result: FactExtraction = llm.generate_structured_output(
        prompt=messages,
        response_schema=FactExtraction,
    )

    return {
        "extracted_facts": result.model_dump()
    }
