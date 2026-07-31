from backend.nodes.generate_questions import generate_questions

# Simulate a state where analysis found gaps
fake_state = {
    "extracted_facts": {
        "has_clear_problem_statement": True,
        "problem_is_ai_solvable": True,
        "problem_category": "nlp",
        "data_availability": "unknown",      # ← gap
        "data_volume_sufficient": "unknown",  # ← gap
        "ai_technique_identified": "unknown", # ← gap
        "requires_new_research": False,
        "integration_complexity": "medium",
        "estimated_effort": "medium",
        "risks_identified": [],
        "extracted_requirements": ["chatbot", "HR answers"],
        "summary": "Team wants a chatbot but data details are unclear",
    },
    "clarification_round": 0,
}

result = generate_questions(fake_state)
print(f"Round: {result['clarification_round']}")  # Should be 1
print(f"Questions generated: {len(result['clarification_questions'])}")
for i, q in enumerate(result["clarification_questions"], 1):
    print(f"  Q{i}: {q}")
