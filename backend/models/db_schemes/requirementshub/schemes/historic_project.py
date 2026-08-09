"""
models/db_schemes/requirementshub/schemes/historic_project.py

SQLAlchemy ORM model for historic AI projects.
Uses pgvector column type for semantic similarity search.
Replaces ChromaDB local persistent store for Cloud Run compatibility.
"""

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, String, Text, JSON
from backend.models.db_schemes.requirementshub.schemes.base import Base
from backend import config


class HistoricProject(Base):
    """
    Stores past AI projects with their embedding vectors for RAG similarity search.

    Design decisions:
    - Vector(EMBEDDING_DIMENSION): Uses cosine distance (<=> operator) via pgvector HNSW index.
    - raw_json (JSON): Preserves the full original dict to reconstruct Python objects at query time.
    - ai_techniques / tags (JSON): Stored as native JSON arrays for future filtering.
    """

    __tablename__ = "historic_projects"

    id = Column(String, primary_key=True)
    project_name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    problem_description = Column(Text, nullable=True)
    solution_description = Column(Text, nullable=True)
    outcome = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    ai_techniques = Column(JSON, nullable=True)  # list[str]
    tags = Column(JSON, nullable=True)            # list[str]
    raw_json = Column(JSON, nullable=True)        # Full snapshot of original project dict
    embedding = Column(
        Vector(config.EMBEDDING_DIMENSION),
        nullable=True,
        comment="Cosine embedding from Gemini text-embedding-004"
    )
