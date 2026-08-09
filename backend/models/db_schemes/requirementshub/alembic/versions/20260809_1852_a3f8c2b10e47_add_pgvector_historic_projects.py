"""Add pgvector extension and historic_projects table

Revision ID: a3f8c2b10e47
Revises: dbc59de56c9b
Create Date: 2026-08-09 18:52:00.000000+00:00

Installs the pgvector PostgreSQL extension and creates the historic_projects
table with a VECTOR(768) embedding column and an HNSW cosine distance index.
This replaces the ChromaDB local file store for stateless Cloud Run deployments.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "a3f8c2b10e47"
down_revision: Union[str, None] = "dbc59de56c9b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Step 1: Enable pgvector extension ─────────────────────────────────────
    # Required once per PostgreSQL database instance.
    # On Cloud SQL, the extension is already available.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── Step 2: Create historic_projects table ─────────────────────────────────
    op.create_table(
        "historic_projects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_name", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("problem_description", sa.Text(), nullable=True),
        sa.Column("solution_description", sa.Text(), nullable=True),
        sa.Column("outcome", sa.String(), nullable=True),
        sa.Column("contact_person", sa.String(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("ai_techniques", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── Step 3: HNSW index for approximate nearest-neighbor cosine search ──────
    # HNSW (Hierarchical Navigable Small World) is significantly faster than
    # the default flat index for large datasets (> 1000 vectors).
    # vector_cosine_ops aligns with <=> operator used in search_similar().
    op.execute(
        "CREATE INDEX idx_historic_projects_embedding_hnsw "
        "ON historic_projects USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_table("historic_projects")
    # Note: We intentionally do NOT drop the vector extension on downgrade
    # as other tables or features might depend on it.
