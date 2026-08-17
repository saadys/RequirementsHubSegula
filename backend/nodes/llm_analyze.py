"""
LLM Analyze Node

Calls the LLM with structured output to extract FactExtraction from the
business team's request. Uses department-specific prompts and RAG context.

Owner: Track A
"""

from typing import Any, Dict, Iterator
from backend.contracts.state import PipelineState
from backend.schemas import CategoricalFactExtraction
from backend.services.llm import get_structured_llm
from backend import config
from backend.LLM.templates.corporate_support import get_prompt as get_corporate_support_prompt


def get_llm_analyze_messages(state: PipelineState) -> list:
    """Constructs prompt messages for 5-pillar fact extraction."""
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
    return prompt_builder(
        form_data=form_data,
        similar_projects=filtered_projects if filtered_projects else None,
        clarification_round=clarification_round,
        clarification_answers=clarification_answers,
        clarification_questions=clarification_questions,
    )


def stream_llm_analyze(state: PipelineState) -> Iterator[Dict[str, Any]]:
    """Streams 5-pillar reasoning tokens in real-time and yields final extracted facts."""
    messages = get_llm_analyze_messages(state)
    llm = get_structured_llm()
    for event in llm.generate_structured_output_stream(
        prompt=messages,
        response_schema=CategoricalFactExtraction,
    ):
        if event.get("type") == "thinking":
            yield {"type": "thinking", "content": event.get("content", "")}
        elif event.get("type") == "result":
            extracted = event.get("data")
            yield {
                "type": "result",
                "data": {
                    "extracted_facts": extracted.model_dump() if hasattr(extracted, "model_dump") else extracted
                },
            }


def llm_analyze(state: PipelineState) -> dict:
    """Node that invokes the structured LLM to extract 5-pillar categorical facts from the request."""
    messages = get_llm_analyze_messages(state)
    llm = get_structured_llm()
    result: CategoricalFactExtraction = llm.generate_structured_output(
        prompt=messages,
        response_schema=CategoricalFactExtraction,
    )

    return {
        "extracted_facts": result.model_dump()
    }
