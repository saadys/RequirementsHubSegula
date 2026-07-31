from backend.services.vectorstore import get_collection

collection = get_collection()
print(f"Collection: {collection.name}")
print(f"Count: {collection.count()}")

# Manual test: add one doc, query it
collection.add(
    documents=["AI chatbot for internal HR document search"],
    ids=["test-001"],
    metadatas=[{"project": "test"}]
)
print(f"Count after add: {collection.count()}")

results = collection.query(query_texts=["AI chatbot for HR document search"], n_results=1)
print(f"Query result: {results['documents']}")
print(f"Distance: {results['distances']}")

# Cleanup
collection.delete(ids=["test-001"])
print(f"Count after delete: {collection.count()}")
