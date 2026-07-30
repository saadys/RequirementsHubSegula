"""
RAG Search Node

Embeds the request, queries ChromaDB, returns similar historic projects.
Determines if an exact match exists (score >= 0.95).

Owner: Track A
"""

from backend.contracts.state import PipelineState
from backend.services.vectorstore import search_similar
from backend import config


def rag_search(state: PipelineState) -> dict:
    """Node that searches ChromaDB for historic projects similar to the submitted request."""
    form_data = state.get("form_data", {})
    problem_desc = form_data.get("problem_description", "")
    parsed_files = state.get("parsed_files_text", [])
    
    # Build search query string from problem description and uploaded file content
    query_parts = [problem_desc]
    if parsed_files:
        query_parts.extend(parsed_files)
        
    query = " ".join(query_parts).strip()
    
    # Query ChromaDB for top-K similar projects
    results = search_similar(query, top_k=config.RAG_TOP_K)
    
    similar_projects = []
    rag_scores = []
    is_exact_match = False
    exact_match_project = None
    
    for doc, score, meta in results:
        similar_projects.append(meta)
        rag_scores.append(float(score))
        
        # Check if score meets exact match threshold (e.g., >= 0.95)
        if score >= config.RAG_EXACT_MATCH_THRESHOLD and not is_exact_match:
            is_exact_match = True
            exact_match_project = meta
            
    return {
        "similar_projects": similar_projects,
        "rag_scores": rag_scores,
        "is_exact_match": is_exact_match,
        "exact_match_project": exact_match_project,
    }
