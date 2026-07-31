from backend.nodes.generate_report import generate_report

# Simulate a full state after Track A (LLM/RAG) and Track B (Scoring)
fake_state = {
    "form_data": {
        "project_name": "Smart Onboarding Bot",
        "department": "Corporate & Support Services",
        "team_contact_name": "Dupont Jean",
        "team_contact_email": "jean.dupont@segula.fr",
        "problem_description": "New employees waste time asking colleagues HR questions.",
    },
    "extracted_facts": {
        "summary": "The team requires an AI chatbot to automate responses to common HR onboarding questions using existing policy documents.",
        "problem_category": "nlp",
        "ai_technique_identified": "RAG-based document retrieval with LLM",
        "data_availability": "full",
        "integration_complexity": "medium",
        "estimated_effort": "medium",
        "extracted_requirements": [
            "Must answer HR onboarding queries",
            "Response time under 10 seconds",
            "Integrate with SharePoint policy docs"
        ],
        "risks_identified": [
            "GDPR compliance regarding employee data",
            "LLM hallucination risk on policy details",
            "Role-based access control requirement"
        ]
    },
    "score": 85,
    "score_breakdown": {
        "problem_clarity": {"score": 20, "max": 20},
        "ai_solvability": {"score": 15, "max": 15},
        "data_availability": {"score": 20, "max": 20},
        "similar_projects": {"score": 12, "max": 15},
        "research_needed": {"score": 10, "max": 10},
        "technique_clarity": {"score": 10, "max": 10},
        "integration": {"score": 7, "max": 10},
    },
    "decision": "GO",
    "similar_projects": [
        {
            "project_name": "IRFANE Chatbot",
            "solution_description": "Multi-agent HR and IT document search chatbot.",
            "contact_person": "ABBAR Wissale"
        }
    ]
}

result = generate_report(fake_state)
print(f"Report Type: {result['report_type']}")
print("\n" + "=" * 60)
print(result["report"])
print("=" * 60)
