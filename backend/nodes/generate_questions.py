"""
Generate Questions Node

When feasibility score is 40-69, generates targeted clarification questions
based on gaps identified in the extracted facts.

Owner: Track A
"""

# TODO [Track A]: Implement generate_questions node
#
# Input from state: extracted_facts, clarification_round
# Output to state: clarification_questions, clarification_round (incremented)
#
# def generate_questions(state: PipelineState) -> dict:
#     1. Identify weak/unknown fields in extracted_facts
#     2. Call clarification_llm.invoke() → ClarificationQuestions
#     3. Return {"clarification_questions": [...], "clarification_round": round + 1}
