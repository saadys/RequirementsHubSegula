from backend.services.vectorstore import load_seed_data
from backend.nodes.rag_search import rag_search
from backend.nodes.fast_track import fast_track
from backend.nodes.llm_analyze import llm_analyze
from backend.nodes.generate_questions import generate_questions

load_seed_data()

print("=" * 60)
print("RUNNING END-TO-END TRACK A CHAIN TESTS")
print("=" * 60)

# === Scenario 1: High similarity / Exact match test ===
print("\n--- Scenario 1: Potential Fast-Track / High Similarity ---")
state_1 = {
    "form_data": {
        "project_name": "Recruitment AI",
        "department": "corporate_support",
        "problem_description": "We need a multi-agent system for recruitment with CV scoring, bias detection, and automated coding tests for candidates",
        "current_process": "Manual ATS and HR screening",
        "expected_outcome": "Fully automated recruitment pipeline",
    },
    "parsed_files_text": [],
    "department": "corporate_support",
    "clarification_round": 0,
    "clarification_answers": [],
}

state_1.update(rag_search(state_1))
print(f"Top RAG Score: {state_1['rag_scores'][0]:.4f} (Threshold: 0.95)")
print(f"Exact match triggered: {state_1['is_exact_match']}")
if state_1["is_exact_match"]:
    result = fast_track(state_1)
    print(f"  → Fast track report generated ({len(result['report'])} chars)")
else:
    print(f"  → Score did not reach 0.95 exact match threshold. Closest match: '{state_1['similar_projects'][0].get('project_name')}'")


# === Scenario 2: Similar but not exact (Full LLM Analysis) ===
print("\n--- Scenario 2: Standard Request (Full LLM Analysis) ---")
state_2 = {
    "form_data": {
        "project_name": "Knowledge Bot",
        "department": "corporate_support",
        "problem_description": "IT support team gets 200 tickets/day for common questions. We want a chatbot to handle L1 support automatically.",
        "current_process": "IT team manually answers tickets via Jira",
        "expected_outcome": "80% of L1 tickets resolved by AI chatbot",
        "data_description": "3 years of Jira tickets + IT wiki",
    },
    "parsed_files_text": [],
    "department": "corporate_support",
    "clarification_round": 0,
    "clarification_answers": [],
}

state_2.update(rag_search(state_2))
print(f"RAG Top Score: {state_2['rag_scores'][0]:.4f}")
print(f"Exact match triggered: {state_2['is_exact_match']}")

state_2.update(llm_analyze(state_2))
facts_2 = state_2['extracted_facts']
print(f"  → Facts extracted successfully.")
print(f"    - Category: {facts_2['problem_category']}")
print(f"    - Technique: {facts_2['ai_technique_identified']}")
print(f"    - Data Availability: {facts_2['data_availability']}")
print(f"    - Effort: {facts_2['estimated_effort']}")
print(f"    - Summary: {facts_2['summary']}")


# === Scenario 3: Vague request (Triggers Clarification Questions) ===
print("\n--- Scenario 3: Vague Request (Clarification Generation) ---")
state_3 = {
    "form_data": {
        "project_name": "AI Thing",
        "department": "corporate_support",
        "problem_description": "We want to use AI for something in HR",
        "current_process": "Unknown",
        "expected_outcome": "Better",
    },
    "parsed_files_text": [],
    "department": "corporate_support",
    "clarification_round": 0,
    "clarification_answers": [],
}

state_3.update(rag_search(state_3))
state_3.update(llm_analyze(state_3))
facts_3 = state_3['extracted_facts']
print(f"  → Problem clear: {facts_3['has_clear_problem_statement']}")
print(f"  → Data availability: {facts_3['data_availability']}")

# Simulate that scoring engine returned NEEDS_CLARIFICATION
result_3 = generate_questions(state_3)
print(f"  → Clarification Round: {result_3['clarification_round']}")
print(f"  → Generated {len(result_3['clarification_questions'])} clarification questions:")
for i, q in enumerate(result_3["clarification_questions"], 1):
    print(f"    Q{i}: {q}")

print("\n" + "=" * 60)
print("✅ Track A End-to-End Execution Complete!")
print("=" * 60)
