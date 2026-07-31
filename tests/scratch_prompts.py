from backend.prompts.corporate_support import get_prompt

messages = get_prompt(
    form_data={
        "project_name": "Smart Onboarding",
        "problem_description": "New employees waste 2 weeks finding HR info",
        "current_process": "Ask colleagues",
        "expected_outcome": "Instant answers via chatbot",
    },
    similar_projects=[
        {"project_name": "IRFANE", "solution_description": "Multi-agent chatbot..."}
    ],
    clarification_answers=[],
)

for msg in messages:
    print(f"[{msg['role']}] {msg['content'][:200]}...")