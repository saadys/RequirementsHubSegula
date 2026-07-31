from backend.services.vectorstore import load_seed_data, search_similar, get_collection

# Load all 4 projects
load_seed_data()
collection = get_collection()
print(f"Projects loaded: {collection.count()}")  # Should be 4

# Test: query that should match Talentium
results = search_similar("We need AI to screen CVs and score candidates", top_k=2)
print("\nQuery: 'We need AI to screen CVs and score candidates'")
for doc, score, meta in results:
    print(f"  {score:.3f} | {meta.get('project_name', 'unknown')}")

# Test: query that should match IRFANE
results = search_similar("chatbot for new employee onboarding", top_k=2)
print("\nQuery: 'chatbot for new employee onboarding'")
for doc, score, meta in results:
    print(f"  {score:.3f} | {meta.get('project_name', 'unknown')}")

# Test: query that should match nothing closely
results = search_similar("automate financial quarterly reports", top_k=2)
print("\nQuery: 'automate financial quarterly reports'")
for doc, score, meta in results:
    print(f"  {score:.3f} | {meta.get('project_name', 'unknown')}")
