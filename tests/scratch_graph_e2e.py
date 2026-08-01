"""
End-to-End Graph Test

Tests the full compiled LangGraph pipeline across 3 scenarios:
1. Complete GO request → full report
2. Vague request → NEEDS_CLARIFICATION → questions generated
3. Incomplete form → stops at validation
"""


from backend.graph.builder import get_compiled_graph

graph = get_compiled_graph()

print("=" * 60)
print("LANGGRAPH END-TO-END PIPELINE TEST")
print("=" * 60)

# ═══════════════════════════════════════════════════════════════
# Scenario 1: Complete, clear request → Should reach GO report
# ═══════════════════════════════════════════════════════════════
print("\n--- Scenario 1: Clear Request (Expecting GO) ---")
state_1 = {
    "form_data": {
        "project_name": "Smart Onboarding Bot",
        "department": "corporate_support",
        "team_contact_name": "Dupont Jean",
        "team_contact_email": "jean.dupont@segula.fr",
        "problem_description": "New employees spend 2 weeks asking colleagues basic HR questions. We want an AI chatbot that answers onboarding questions instantly.",
        "current_process": "Manual: ask colleagues or search SharePoint",
        "expected_outcome": "Chatbot answers HR questions in under 10 seconds",
        "data_description": "We have 500 HR policy documents and an FAQ list",
        "deadline_urgency": "medium",
        "department_specific": {
            "service_area": "hr",
            "target_users": "employees",
            "has_existing_system": True,
        },
    },
    "uploaded_files": [],
    "department": "corporate_support",
    "clarification_round": 0,
    "clarification_answers": [],
}

result_1 = graph.invoke(state_1)
print(f"  Score: {result_1.get('score', 'N/A')}")
print(f"  Decision: {result_1.get('decision', 'N/A')}")
print(f"  Report Type: {result_1.get('report_type', 'N/A')}")
print(f"  Report Length: {len(result_1.get('report', ''))} chars")
print(f"  Is Exact Match: {result_1.get('is_exact_match', 'N/A')}")

# ═══════════════════════════════════════════════════════════════
# Scenario 2: Vague request → Should trigger clarification
# ═══════════════════════════════════════════════════════════════
print("\n--- Scenario 2: Vague Request (Expecting NEEDS_CLARIFICATION) ---")
state_2 = {
    "form_data": {
        "project_name": "AI Thing",
        "department": "corporate_support",
        "team_contact_name": "Martin Sophie",
        "team_contact_email": "sophie.martin@segula.fr",
        "problem_description": "We want to use AI for something in HR",
        "current_process": "Unknown",
        "expected_outcome": "Better",
        "deadline_urgency": "low",
        "department_specific": {
            "service_area": "hr",
            "target_users": "employees",
            "has_existing_system": False,
        },
    },
    "uploaded_files": [],
    "department": "corporate_support",
    "clarification_round": 0,
    "clarification_answers": [],
}

result_2 = graph.invoke(state_2)
print(f"  Score: {result_2.get('score', 'N/A')}")
print(f"  Decision: {result_2.get('decision', 'N/A')}")
print(f"  Clarification Round: {result_2.get('clarification_round', 'N/A')}")
questions = result_2.get("clarification_questions", [])
print(f"  Questions Generated: {len(questions)}")
for i, q in enumerate(questions, 1):
    print(f"    Q{i}: {q}")

# ═══════════════════════════════════════════════════════════════
# Scenario 3: Incomplete form → Should stop at validation
# ═══════════════════════════════════════════════════════════════
print("\n--- Scenario 3: Incomplete Form (Expecting END at validation) ---")
state_3 = {
    "form_data": {
        "project_name": "Half-filled",
        # Missing: team_contact_name, team_contact_email, problem_description, etc.
    },
    "uploaded_files": [],
    "department": "corporate_support",
    "clarification_round": 0,
    "clarification_answers": [],
}

result_3 = graph.invoke(state_3)
print(f"  Is Complete: {result_3.get('is_complete', 'N/A')}")
print(f"  Missing Fields: {result_3.get('missing_fields', [])}")
# Should NOT have score or report since it stopped early
has_score = result_3.get("score") is not None
has_report = result_3.get("report") is not None
print(f"  Reached scoring? {has_score}")
print(f"  Reached report? {has_report}")

print("\n" + "=" * 60)
print("✅ LangGraph Pipeline Test Complete!")
print("=" * 60)
