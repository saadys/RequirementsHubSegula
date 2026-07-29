"""
RAG Search Node

Embeds the request, queries ChromaDB, returns similar historic projects.
Determines if an exact match exists (score >= 0.95).

Owner: Track A
"""

# TODO [Track A]: Implement rag_search node
#
# Input from state: form_data, parsed_files_text, department
# Output to state: similar_projects, rag_scores, is_exact_match, exact_match_project
#
# def rag_search(state: PipelineState) -> dict:
#     1. Build query string from form_data + parsed_files_text
#     2. Call vectorstore.search_similar(query, top_k=RAG_TOP_K)
#     3. Check if any score >= RAG_EXACT_MATCH_THRESHOLD
#     4. Return state updates
