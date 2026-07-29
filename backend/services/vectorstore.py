"""
ChromaDB Vector Store Setup

Manages the historic projects collection for RAG similarity search.

Owner: Track A
"""

# TODO [Track A]: Implement ChromaDB vector store
#
# 1. Initialize ChromaDB client (persistent, data stored in data/chroma/)
# 2. Create/get collection with text-embedding-004 embedding function
# 3. Implement add_project(project: dict) → embeds and stores
# 4. Implement search_similar(query: str, top_k: int) → list of (doc, score)
# 5. Implement load_seed_data() → reads historic_projects.json, adds to collection
# 6. Export: get_vectorstore(), search_similar(), load_seed_data()
