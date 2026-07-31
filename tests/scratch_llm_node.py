from backend.services.vectorstore import load_seed_data
from backend.nodes.rag_search import rag_search
from backend.nodes.llm_analyze import llm_analyze

load_seed_data()

# Simulate full pipeline state up to this point
state = {
    "form_data": {
        "project_name": "Smart Onboarding Bot",
        "department": "corporate_support",
        "problem_description": "New employees spend 2 weeks asking colleagues basic HR questions. We want an AI chatbot.",
        "current_process": "Manual: ask colleagues or search SharePoint",
        "expected_outcome": "Chatbot that answers HR questions in under 10 seconds",
        "data_description": "We have 500 HR policy documents and an FAQ list",
    },
    "parsed_files_text": [],
    "department": "corporate_support",
    "clarification_round": 0,
    "clarification_answers": [],
}

# Run RAG first
state.update(rag_search(state))
print(f"RAG found {len(state['similar_projects'])} similar projects")

# Run LLM analysis
result = llm_analyze(state)
facts = result["extracted_facts"]
print(f"\n--- Extracted Facts ---")
print(f"Clear problem: {facts['has_clear_problem_statement']}")
print(f"AI solvable: {facts['problem_is_ai_solvable']}")
print(f"Category: {facts['problem_category']}")
print(f"Data: {facts['data_availability']}")
print(f"Technique: {facts['ai_technique_identified']}")
print(f"Effort: {facts['estimated_effort']}")
print(f"Summary: {facts['summary']}")
print(f"Requirements: {facts['extracted_requirements']}")
print(f"Risks: {facts['risks_identified']}")
