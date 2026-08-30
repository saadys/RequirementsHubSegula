"""Align fact_extractions column types with the ORM models

Revision ID: d5b2f9c8e320
Revises: c4a1e8b7d219
Create Date: 2026-08-25 03:01:00.000000+00:00

The models were widened without a matching revision, leaving the deployed
schema behind:

  - identified_technique     VARCHAR(200) -> Text
  - ai_technique_identified  VARCHAR(100) -> Text
  - raw_extraction           JSON         -> JSONB

The VARCHAR limits truncate nothing silently -- PostgreSQL raises on
over-length values -- so an LLM returning a longer technique label fails the
INSERT at runtime. JSONB additionally allows indexing and avoids reparsing the
document on every read.

All three widen the accepted domain, so they are backward-compatible with a
still-running previous application revision. The downgrade narrows them back
and can therefore fail on rows that already exceed the old limits; that is
intentional rather than a silent truncation.

Also syncs the `historic_projects.embedding` column comment, which existed on
the model but never in the database. Autogenerate compares comments and has no
opt-out, so leaving it unsynced would keep `alembic check` permanently red and
hide real drift behind a known-noisy diff.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d5b2f9c8e320"
down_revision: Union[str, None] = "c4a1e8b7d219"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "fact_extractions",
        "identified_technique",
        existing_type=sa.VARCHAR(length=200),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "fact_extractions",
        "ai_technique_identified",
        existing_type=sa.VARCHAR(length=100),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "fact_extractions",
        "raw_extraction",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        postgresql_using="raw_extraction::jsonb",
    )
    op.alter_column(
        "historic_projects",
        "embedding",
        existing_type=Vector(768),
        type_=Vector(1024),
        existing_nullable=True,
        comment="Cosine embedding from Gemini text-embedding-004",
    )


def downgrade() -> None:
    op.alter_column(
        "historic_projects",
        "embedding",
        existing_type=Vector(1024),
        type_=Vector(768),
        existing_nullable=True,
        comment="Cosine embedding from Gemini text-embedding-004",
    )
    op.alter_column(
        "fact_extractions",
        "raw_extraction",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=postgresql.JSON(astext_type=sa.Text()),
        existing_nullable=False,
        postgresql_using="raw_extraction::json",
    )
    op.alter_column(
        "fact_extractions",
        "ai_technique_identified",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=100),
        existing_nullable=True,
        postgresql_using="SUBSTRING(ai_technique_identified FROM 1 FOR 100)",
    )
    op.alter_column(
        "fact_extractions",
        "identified_technique",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=200),
        existing_nullable=True,
        postgresql_using="SUBSTRING(identified_technique FROM 1 FOR 200)",
    )
