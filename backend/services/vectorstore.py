"""
backend/services/vectorstore.py

Vector Store Service — pgvector implementation.

Replaces the previous ChromaDB PersistentClient with a fully stateless
async pgvector implementation backed by Cloud SQL PostgreSQL.

Key design decisions:
- Stateless: No local filesystem dependency. Compatible with Cloud Run.
- Async: All DB operations use SQLAlchemy AsyncSession (asyncpg driver).
- Cosine similarity: Uses pgvector <=> operator + HNSW index for fast ANN search.
- google-genai SDK: Replaces deprecated google-generativeai package.
"""

import json
import logging
from typing import Any

from google import genai as google_genai
from google.genai import types as genai_types
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend import config
from backend.models.db_schemes.requirementshub.schemes.historic_project import HistoricProject

logger = logging.getLogger("backend.services.vectorstore")


# ── Embedding Client ──────────────────────────────────────────────────────────

def _get_genai_client() -> google_genai.Client:
    """
    Builds a google-genai Client with key rotation.
    Tries GEMINI_API_KEY_1 first, falls back to GEMINI_API_KEY_2.
    On Cloud Run with Vertex AI, ADC (Application Default Credentials) are used
    automatically if no API key is set.
    """
    api_key = config.GEMINI_API_KEY_1 or config.GEMINI_API_KEY_2
    if api_key:
        return google_genai.Client(api_key=api_key)
    # Fallback to Application Default Credentials (Cloud Run IAM)
    return google_genai.Client()


import math
import asyncio


def is_valid_embedding(embedding: Any, expected_dim: int) -> bool:
    """Validates that an embedding is present, matches expected dimension, and has a normalized unit norm."""
    if embedding is None:
        return False
    try:
        vec = embedding
        if isinstance(vec, str):
            vec = json.loads(vec)
        if hasattr(vec, "tolist"):
            vec = vec.tolist()
        if not hasattr(vec, "__len__") or len(vec) != expected_dim:
            return False
        # Valid unit embeddings (e.g. Qwen3) have a vector norm ≈ 1.0 (allow 0.7 - 1.3)
        norm = math.sqrt(sum(float(x) ** 2 for x in vec))
        return 0.7 <= norm <= 1.3
    except Exception:
        return False


async def generate_embedding(text_input: str) -> list[float]:
    """
    Generates an embedding vector for the given text with automated retries.

    Routes on config.LLM_BACKEND: native Ollama endpoint (/api/embed) for Qwen3-Embedding.
    Falls back to Gemini text-embedding if configured.
    Zero silent random float corruption.
    """
    last_error: Exception | None = None

    if config.LLM_BACKEND in (config.BACKEND_OLLAMA_LOCAL, config.BACKEND_LIGHTNING_VLLM) or config.USE_LOCAL_LLM:
        import httpx

        model_name = getattr(config, "LOCAL_EMBEDDING_MODEL", "qwen3-embedding:0.6b")
        base_url = getattr(config, "OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        url = f"{base_url}/api/embed"
        api_key = getattr(config, "OLLAMA_API_KEY", "")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Up to 3 attempts with exponential backoff (1s, 2s, 4s)
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        url,
                        json={"model": model_name, "input": text_input},
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        embeddings = data.get("embeddings", [])
                        if embeddings and len(embeddings[0]) == config.EMBEDDING_DIMENSION:
                            return embeddings[0]
                    logger.warning(
                        "[VectorStore] Sovereign embedding attempt %d/3 failed with status %d: %s",
                        attempt + 1,
                        resp.status_code,
                        resp.text,
                    )
                    last_error = RuntimeError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")
            except Exception as exc:
                logger.warning("[VectorStore] Sovereign embedding attempt %d/3 failed: %s", attempt + 1, exc)
                last_error = exc

            if attempt < 2:
                await asyncio.sleep(1.0 * (2 ** attempt))

    keys_to_try = [k for k in [config.GEMINI_API_KEY_1, config.GEMINI_API_KEY_2] if k]
    if keys_to_try:
        model_name = getattr(config, "EMBEDDING_MODEL", "models/text-embedding-004").removeprefix("models/").removeprefix("gemini/")
        for key in keys_to_try:
            try:
                client = google_genai.Client(api_key=key)
                response = client.models.embed_content(
                    model=model_name,
                    contents=text_input,
                    config=genai_types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=config.EMBEDDING_DIMENSION,
                    ),
                )
                return response.embeddings[0].values
            except Exception as exc:
                logger.warning("Embedding key failed (%s) with model %s, trying next: %s", key[:8], model_name, exc)
                last_error = exc

    raise RuntimeError(
        f"All embedding methods failed. Sovereign Ollama endpoint at '{getattr(config, 'OLLAMA_BASE_URL', '')}' "
        f"is unreachable. Ensure Lightning AI Studio is active and port 8000 is Public. Last error: {last_error}"
    )


# ── Seed Data ─────────────────────────────────────────────────────────────────

async def load_seed_data(db: AsyncSession) -> None:
    """
    Reads historic_projects.json and upserts all projects into the
    historic_projects PostgreSQL table with verified embeddings.

    Self-Healing:
    - If a project already exists with a valid embedding, it is skipped.
    - If a project exists with a missing or corrupted embedding, it is automatically re-embedded and updated.
    - If a project is new, it is embedded and inserted.
    """
    with open(config.HISTORIC_PROJECTS_PATH, "r") as f:
        projects: list[dict[str, Any]] = json.load(f)

    inserted = 0
    updated = 0
    skipped = 0

    for project in projects:
        doc_string = (
            f"Problem: {project['problem_description']}\n"
            f"Solution: {project['solution_description']}\n"
            f"Tags: {', '.join(project['tags'])}"
        )

        existing = await db.get(HistoricProject, project["id"])
        if existing is not None:
            # Self-healing: verify vector validity (dimension & unit norm)
            if is_valid_embedding(existing.embedding, config.EMBEDDING_DIMENSION):
                skipped += 1
                continue
            logger.warning(
                "[VectorStore] Detected missing/corrupted embedding for project '%s'. Triggering self-healing...",
                project["id"],
            )

        # Generate verified embedding
        embedding_vector = await generate_embedding(doc_string)

        if existing is not None:
            existing.embedding = embedding_vector
            existing.project_name = project["project_name"]
            existing.department = project.get("department")
            existing.problem_description = project.get("problem_description")
            existing.solution_description = project.get("solution_description")
            existing.outcome = project.get("outcome")
            existing.contact_person = project.get("contact_person")
            existing.year = project.get("year")
            existing.ai_techniques = project.get("ai_techniques", [])
            existing.tags = project.get("tags", [])
            existing.raw_json = project
            updated += 1
        else:
            record = HistoricProject(
                id=project["id"],
                project_name=project["project_name"],
                department=project.get("department"),
                problem_description=project.get("problem_description"),
                solution_description=project.get("solution_description"),
                outcome=project.get("outcome"),
                contact_person=project.get("contact_person"),
                year=project.get("year"),
                ai_techniques=project.get("ai_techniques", []),
                tags=project.get("tags", []),
                raw_json=project,
                embedding=embedding_vector,
            )
            db.add(record)
            inserted += 1

    await db.commit()
    logger.info(
        "[VectorStore] Seed complete — %d inserted, %d self-healed, %d already verified.",
        inserted,
        updated,
        skipped,
    )


# ── Ingest Delivered Project ──────────────────────────────────────────────────

async def ingest_project(
    submission_id: str,
    project_data: Any,
    db: AsyncSession,
) -> tuple[HistoricProject, str]:
    """
    Ingests a successfully delivered project into the PostgreSQL historic_projects table.

    Workflow:
    1. Builds a rich semantic document string combining all delivered project aspects.
    2. Generates a 768-dim embedding via Gemini text-embedding-004 in memory (stateless).
    3. Merges/Inserts the record into the historic_projects pgvector table.
    4. Updates the originating Submission status to 'IMPLEMENTED'.
    5. Commits atomically so the project is immediately queryable via HNSW index.

    Returns:
        tuple[HistoricProject, str]: (merged_historic_record, generated_historic_id)
    """
    import datetime
    import uuid as uuid_pkg
    from backend.models.db_schemes.requirementshub.schemes.submission import Submission
    from backend.schemas.Enums import SubmissionStatus

    if hasattr(project_data, "model_dump"):
        data = project_data.model_dump()
    elif isinstance(project_data, dict):
        data = project_data
    else:
        data = dict(project_data)

    current_year = data.get("year") or datetime.datetime.now(datetime.timezone.utc).year
    short_suffix = str(submission_id).replace("-", "")[:8].upper()
    historic_id = f"HIST-{current_year}-{short_suffix}"

    ai_tech_list = data.get("ai_techniques") or []
    tags_list = data.get("tags") or []

    doc_string = (
        f"Project: {data.get('project_name')}\n"
        f"Department: {data.get('department')}\n"
        f"Problem: {data.get('problem_description')}\n"
        f"Solution: {data.get('solution_description')}\n"
        f"Outcome: {data.get('outcome')}\n"
        f"AI Techniques: {', '.join(ai_tech_list)}\n"
        f"Tags: {', '.join(tags_list)}\n"
        f"Lessons Learned: {data.get('lessons_learned') or 'N/A'}"
    )

    embedding_vector = await generate_embedding(doc_string)

    record = HistoricProject(
        id=historic_id,
        project_name=data.get("project_name", "Delivered Project"),
        department=data.get("department"),
        problem_description=data.get("problem_description"),
        solution_description=data.get("solution_description"),
        outcome=data.get("outcome"),
        contact_person=data.get("contact_person"),
        year=current_year,
        ai_techniques=ai_tech_list,
        tags=tags_list,
        raw_json={
            "id": historic_id,
            "submission_id": str(submission_id),
            "project_name": data.get("project_name"),
            "department": data.get("department"),
            "problem_description": data.get("problem_description"),
            "solution_description": data.get("solution_description"),
            "outcome": data.get("outcome"),
            "contact_person": data.get("contact_person"),
            "year": current_year,
            "ai_techniques": ai_tech_list,
            "tags": tags_list,
            "lessons_learned": data.get("lessons_learned"),
        },
        embedding=embedding_vector,
    )

    merged_record = await db.merge(record)

    # Update originating submission status if found
    try:
        sub_uuid = uuid_pkg.UUID(str(submission_id))
    except (ValueError, TypeError):
        sub_uuid = submission_id

    sub = await db.get(Submission, sub_uuid)
    if sub is not None:
        sub.status = SubmissionStatus.IMPLEMENTED.value

    await db.commit()
    await db.refresh(merged_record)

    logger.info(
        "[VectorStore] Successfully ingested project '%s' (%s) into pgvector knowledge base.",
        data.get("project_name"),
        historic_id,
    )
    return merged_record, historic_id


# ── Search ────────────────────────────────────────────────────────────────────

async def search_similar(
    query: str,
    top_k: int,
    db: AsyncSession,
) -> list[tuple[str, float, dict]]:
    """
    Searches the historic_projects table for vectors closest to the query embedding.

    Uses pgvector cosine distance operator (<=>).
    Cosine similarity = 1 - cosine_distance.

    Returns:
        list of (doc_string, similarity_score, metadata_dict)
        sorted by descending similarity (closest first).
    """
    if db.bind and db.bind.dialect.name == "sqlite":
        logger.debug("[VectorStore] SQLite database detected in test session. Skipping pgvector operator.")
        return []

    query_embedding = await generate_embedding(query)

    # SQLAlchemy raw SQL with pgvector <=> cosine distance operator
    # The HNSW index on `embedding` makes this approximate (fast at scale).
    stmt = text(
        """
        SELECT
            id,
            project_name,
            problem_description,
            solution_description,
            tags,
            raw_json,
            1 - (embedding <=> CAST(:query_vec AS vector)) AS similarity
        FROM historic_projects
        ORDER BY embedding <=> CAST(:query_vec AS vector)
        LIMIT :top_k
        """
    )

    result = await db.execute(
        stmt,
        {
            "query_vec": str(query_embedding),
            "top_k": top_k,
        },
    )
    rows = result.fetchall()

    output = []
    for row in rows:
        doc_string = (
            f"Problem: {row.problem_description}\n"
            f"Solution: {row.solution_description}\n"
            f"Tags: {row.tags}"
        )
        score = float(row.similarity)
        metadata = row.raw_json if row.raw_json else {"id": row.id, "project_name": row.project_name}

        output.append((doc_string, score, metadata))

    return output


# ── Healthcheck helper ────────────────────────────────────────────────────────

async def is_seed_data_loaded(db: AsyncSession) -> bool:
    """Returns True if at least one project has been indexed in the DB."""
    result = await db.execute(text("SELECT COUNT(*) FROM historic_projects"))
    count = result.scalar()
    return (count or 0) > 0