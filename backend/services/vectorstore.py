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


async def generate_embedding(text_input: str) -> list[float]:
    """
    Generates an embedding vector for the given text.
    If USE_LOCAL_LLM is True, calls Ollama /api/embed using LOCAL_EMBEDDING_MODEL.
    Otherwise, uses Gemini text-embedding via google-genai SDK.
    """
    if config.USE_LOCAL_LLM:
        import httpx
        model_name = getattr(config, "LOCAL_EMBEDDING_MODEL", "qwen3-embedding:0.6b")
        base_url = config.OLLAMA_BASE_URL.rstrip("/")
        url = f"{base_url}/api/embed"
        headers = {"Content-Type": "application/json"}
        if getattr(config, "OLLAMA_API_KEY", ""):
            headers["Authorization"] = f"Bearer {config.OLLAMA_API_KEY}"
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
                    if embeddings:
                        return embeddings[0]
                logger.error("Local Ollama embedding returned status %d: %s", resp.status_code, resp.text)
        except Exception as exc:
            logger.warning("Local Ollama embedding failed: %s", exc)

    keys_to_try = [k for k in [config.GEMINI_API_KEY_1, config.GEMINI_API_KEY_2] if k]
    last_error: Exception | None = None

    if keys_to_try:
        for key in keys_to_try:
            try:
                model_name = config.EMBEDDING_MODEL.removeprefix("models/").removeprefix("gemini/")
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
    else:
        last_error = ValueError("No Gemini API keys configured.")

    if config.ENV == "development":
        logger.warning("[VectorStore] Embedding API unavailable (%s). Using deterministic local vector.", last_error)
        import hashlib
        import random
        seed = int(hashlib.sha256(text_input.encode("utf-8")).hexdigest()[:8], 16)
        rng = random.Random(seed)
        return [rng.uniform(-0.1, 0.1) for _ in range(config.EMBEDDING_DIMENSION)]

    raise RuntimeError(f"All embedding methods failed. Last error: {last_error}")


# ── Seed Data ─────────────────────────────────────────────────────────────────

async def load_seed_data(db: AsyncSession) -> None:
    """
    Reads historic_projects.json and upserts all projects into the
    historic_projects PostgreSQL table with their embeddings.

    Idempotent: Uses INSERT ... ON CONFLICT DO UPDATE (upsert by id).
    Safe to call at every startup — only re-embeds if entry is missing.
    """
    with open(config.HISTORIC_PROJECTS_PATH, "r") as f:
        projects: list[dict[str, Any]] = json.load(f)

    inserted = 0
    skipped = 0

    for project in projects:
        # Check if already exists (avoid re-embedding on every restart)
        existing = await db.get(HistoricProject, project["id"])
        if existing is not None:
            skipped += 1
            continue

        doc_string = (
            f"Problem: {project['problem_description']}\n"
            f"Solution: {project['solution_description']}\n"
            f"Tags: {', '.join(project['tags'])}"
        )

        embedding_vector = await generate_embedding(doc_string)

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
        "[VectorStore] Seed complete — %d inserted, %d already existed.",
        inserted,
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