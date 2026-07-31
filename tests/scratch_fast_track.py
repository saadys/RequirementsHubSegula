from backend.nodes.fast_track import fast_track

fake_state = {
    "exact_match_project": {
        "project_name": "Talentium",
        "solution_description": "Multi-agent recruitment system with CV scoring...",
        "contact_person": "ABBAR Wissale / KETATNI Maryam",
        "outcome": "successful",
        "ai_techniques": ["multi-agent", "llm-scoring", "bias-detection"],
    }
}

result = fast_track(fake_state)
print(f"Report Type: {result['report_type']}")
print("\n--- Formatted Report ---")
print(result["report"])
