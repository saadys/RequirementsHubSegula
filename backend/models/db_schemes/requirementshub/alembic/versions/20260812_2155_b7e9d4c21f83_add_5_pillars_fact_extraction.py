"""Add 5 categorical feasibility pillars to fact_extractions table

Revision ID: b7e9d4c21f83
Revises: a3f8c2b10e47
Create Date: 2026-08-12 21:55:00.000000+00:00

Adds the 5-pillar categorical evaluation columns (AI Viability, Data Readiness,
Problem Clarity, Integration Feasibility, Governance & Safety) and structured
raw_extraction JSON payload to the fact_extractions table.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7e9d4c21f83"
down_revision: Union[str, None] = "a3f8c2b10e47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 5-Pillar columns
    op.add_column("fact_extractions", sa.Column("ai_viability_category", sa.String(50), nullable=True))
    op.add_column("fact_extractions", sa.Column("ai_viability_reason", sa.Text(), nullable=True))

    op.add_column("fact_extractions", sa.Column("data_readiness_category", sa.String(50), nullable=True))
    op.add_column("fact_extractions", sa.Column("data_readiness_reason", sa.Text(), nullable=True))

    op.add_column("fact_extractions", sa.Column("problem_clarity_category", sa.String(50), nullable=True))
    op.add_column("fact_extractions", sa.Column("problem_clarity_reason", sa.Text(), nullable=True))

    op.add_column("fact_extractions", sa.Column("integration_category", sa.String(50), nullable=True))
    op.add_column("fact_extractions", sa.Column("integration_reason", sa.Text(), nullable=True))

    op.add_column("fact_extractions", sa.Column("governance_category", sa.String(50), nullable=True))
    op.add_column("fact_extractions", sa.Column("governance_reason", sa.Text(), nullable=True))

    # Technical Details
    op.add_column("fact_extractions", sa.Column("identified_technique", sa.String(200), nullable=True))
    op.add_column("fact_extractions", sa.Column("project_summary", sa.Text(), nullable=True))

    # Raw Structured JSON
    op.add_column("fact_extractions", sa.Column("raw_extraction", sa.JSON(), nullable=False, server_default="{}"))


def downgrade() -> None:
    op.drop_column("fact_extractions", "raw_extraction")
    op.drop_column("fact_extractions", "project_summary")
    op.drop_column("fact_extractions", "identified_technique")

    op.drop_column("fact_extractions", "governance_reason")
    op.drop_column("fact_extractions", "governance_category")

    op.drop_column("fact_extractions", "integration_reason")
    op.drop_column("fact_extractions", "integration_category")

    op.drop_column("fact_extractions", "problem_clarity_reason")
    op.drop_column("fact_extractions", "problem_clarity_category")

    op.drop_column("fact_extractions", "data_readiness_reason")
    op.drop_column("fact_extractions", "data_readiness_category")

    op.drop_column("fact_extractions", "ai_viability_reason")
    op.drop_column("fact_extractions", "ai_viability_category")
