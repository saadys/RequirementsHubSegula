"""
RAG Search Node

Embeds the request, queries pgvector (historic_projects table), returns
similar historic projects. Determines if an exact match exists (score >= 0.95).

Owner: Track A
"""

import logging
import time
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional
from backend.models.BaseDataModel import AsyncSessionLocal
from backend.contracts.state import PipelineState
from backend.services.vectorstore import search_similar
from backend import config

logger = logging.getLogger("backend.nodes.rag_search")


async def rag_search(state: PipelineState, db: Optional[AsyncSession] = None) -> dict:
    """
    Async node that queries the pgvector table for historic projects
    similar to the submitted request.
    """
    form_data = state.get("form_data", {})
    problem_desc = form_data.get("problem_description", "")
    project_name = form_data.get("project_name", "")
    expected_outcome = form_data.get("expected_outcome", "")
    current_process = form_data.get("current_process", "")
    parsed_files = state.get("parsed_files_text", [])

    # Build an enriched structured query aligned with historic_projects document structure
    query_parts = []
    if project_name:
        query_parts.append(f"Project: {project_name}")
    if problem_desc:
        query_parts.append(f"Problem: {problem_desc}")
    if expected_outcome:
        query_parts.append(f"Expected Outcome: {expected_outcome}")
    if current_process:
        query_parts.append(f"Current Process: {current_process}")
    if parsed_files:
        query_parts.extend(parsed_files)

    query = "\n".join(query_parts).strip() if query_parts else problem_desc

    start_time = time.perf_counter()
    if db is None:
        async with AsyncSessionLocal() as session:
            results = await search_similar(query, top_k=config.RAG_TOP_K, db=session)
    else:
        results = await search_similar(query, top_k=config.RAG_TOP_K, db=db)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    similar_projects = []
    rag_scores = []
    is_exact_match = False
    exact_match_project = None
    similarity_threshold = config.RAG_SIMILAR_THRESHOLD

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

    top_score = rag_scores[0] if rag_scores else 0.0

    logger.info(
        "RAG search completed | duration_ms=%.2f query_part_count=%d total_results=%d matches_above_threshold=%d top_similarity_score=%.4f threshold=%.2f exact_match=%s",
        duration_ms,
        len(query_parts),
        len(results),
        len(similar_projects),
        top_score,
        similarity_threshold,
        is_exact_match,
    )

    return {
        "similar_projects": similar_projects,
        "rag_scores": rag_scores,
        "is_exact_match": is_exact_match,
        "exact_match_project": exact_match_project,
    }
