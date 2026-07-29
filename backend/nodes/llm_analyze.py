"""
LLM Analyze Node

Calls the LLM with structured output to extract FactExtraction from the
business team's request. Uses department-specific prompts and RAG context.

Owner: Track A
"""

# TODO [Track A]: Implement llm_analyze node
#
# Input from state: form_data, parsed_files_text, department,
#                   similar_projects, clarification_round, clarification_answers
# Output to state: extracted_facts (dict)
#
# def llm_analyze(state: PipelineState) -> dict:
#     1. Load department prompt from prompts/corporate_support.py
#     2. Build context: form_data + file text + similar projects + any clarification answers
#     3. Call structured_llm.invoke(messages) → FactExtraction
#     4. Return {"extracted_facts": result.model_dump()}
