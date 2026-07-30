from backend.services.vectorstore import load_seed_data
from backend.nodes.rag_search import rag_search

load_seed_data()  # ensure data is loaded

# Simulate a state that Track B's parse_input would produce
fake_state = {
    "form_data": {
        "project_name": "Smart Recruiter",
        "department": "corporate_support",
        "problem_description": "We need an AI system to automatically screen CVs, score candidates, and reduce bias in our hiring process",
        "current_process": "Manual CV screening by HR team",
        "expected_outcome": "Automated shortlisting with fairness guarantees",
    },
    "parsed_files_text": [],
    "department": "corporate_support",
}

result = rag_search(fake_state)
print(f"Found {len(result['similar_projects'])} similar projects")
print(f"Top scores: {result['rag_scores'][:3]}")
print(f"Exact match: {result['is_exact_match']}")
if result['is_exact_match']:
    print(f"Matched: {result['exact_match_project']['project_name']}")
else:
    print(f"Closest: {result['similar_projects'][0]['project_name']}")
