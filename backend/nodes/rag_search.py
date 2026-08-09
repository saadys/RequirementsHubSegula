"""
RAG Search Node

Embeds the request, queries pgvector (historic_projects table), returns
similar historic projects. Determines if an exact match exists (score >= 0.95).

Owner: Track A
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from backend.contracts.state import PipelineState
from backend.services.vectorstore import search_similar
from backend import config

logger = logging.getLogger("backend.nodes.rag_search")


async def rag_search(state: PipelineState, db: AsyncSession) -> dict:
    """
    Async node that queries the pgvector table for historic projects
    similar to the submitted request.

    Design: Receives an injected AsyncSession (from FastAPI Depends chain)
    to remain stateless and testable. No global DB state.
    """
    form_data = state.get("form_data", {})
    problem_desc = form_data.get("problem_description", "")
    parsed_files = state.get("parsed_files_text", [])

    # Build search query string from problem description and uploaded file content
    query_parts = [problem_desc]
    if parsed_files:
        query_parts.extend(parsed_files)

    query = " ".join(query_parts).strip()

    # Query pgvector for top-K similar projects via cosine similarity
    results = await search_similar(query, top_k=config.RAG_TOP_K, db=db)

    similar_projects = []
    rag_scores = []
    is_exact_match = False
    exact_match_project = None
    similarity_threshold = getattr(config, "RAG_SIMILAR_THRESHOLD", 0.60)

    for doc, score, meta in results:
        score_val = float(score)
        rag_scores.append(score_val)

        # Only include projects that meet or exceed RAG_SIMILAR_THRESHOLD
        if score_val >= similarity_threshold:
            meta_copy = meta.copy() if meta else {}
            meta_copy["similarity_score"] = round(score_val, 4)
            meta_copy["similarity_percentage"] = round(score_val * 100, 1)
            similar_projects.append(meta_copy)

        # Check if score meets exact match threshold (e.g., >= 0.95)
        if score_val >= config.RAG_EXACT_MATCH_THRESHOLD and not is_exact_match:
            is_exact_match = True
            exact_match_project = meta

    logger.info(
        "[RAG] Query returned %d results. %d above threshold (%.2f). Exact match: %s",
        len(results),
        len(similar_projects),
        similarity_threshold,
        is_exact_match,
    )

    return {
        "similar_projects": similar_projects,
        "rag_scores": rag_scores,
        "is_exact_match": is_exact_match,
        "exact_match_project": exact_match_project,
    }
