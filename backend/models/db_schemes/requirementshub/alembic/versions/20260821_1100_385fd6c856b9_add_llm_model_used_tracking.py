"""Add llm_model_used tracking to fact_extractions and clarification_rounds

Revision ID: 385fd6c856b9
Revises: b7e9d4c21f83
Create Date: 2026-08-21 11:00:00.000000+00:00

Persists which LLM provider/model actually produced a FactExtraction or a
clarification round, so a silent primary->fallback switch (e.g. gemini-flash-lite
-> gpt-4o) is auditable alongside the GO/NO-GO decision it fed, instead of only
appearing as a warning log line.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "385fd6c856b9"
down_revision: Union[str, None] = "b7e9d4c21f83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "fact_extractions",
        sa.Column("llm_model_used", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "clarification_rounds",
        sa.Column("llm_model_used", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clarification_rounds", "llm_model_used")
    op.drop_column("fact_extractions", "llm_model_used")
