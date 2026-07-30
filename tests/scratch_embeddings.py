from backend.services.vectorstore import get_collection

collection = get_collection()

# Add two semantically similar docs and one different
collection.add(
    documents=[
        "AI chatbot for internal HR document search and onboarding",
        "Intelligent assistant that helps new employees find HR policies",
        "Predictive maintenance for factory machines using sensor data",
    ],
    ids=["similar-1", "similar-2", "different-1"],
)

results = collection.query(
    query_texts=["fire hr peaple"],
    n_results=3,
)

print("Query: 'chatbot for employee onboarding'")
for doc, dist in zip(results["documents"][0], results["distances"][0]):
    similarity = 1 - dist  # ChromaDB uses distance, lower = more similar
    print(f"  {similarity:.3f} | {doc[:60]}...")

# similar-1 and similar-2 should score much higher than different-1

# Cleanup
collection.delete(ids=["similar-1", "similar-2", "different-1"])