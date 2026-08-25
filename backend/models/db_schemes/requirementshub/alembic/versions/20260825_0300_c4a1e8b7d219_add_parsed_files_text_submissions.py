"""Add parsed_files_text to submissions

Revision ID: c4a1e8b7d219
Revises: 385fd6c856b9
Create Date: 2026-08-25 03:00:00.000000+00:00

`Submission.parsed_files_text` has been declared on the model and read/written
by the pipeline (routes_stream, routes_clarification, submission_mapper) with
no migration ever creating the column, so any deployed instance raises
UndefinedColumnError on the first submission carrying uploaded documents.

The column is NOT NULL to match the model, which forces a server_default for
the backfill of existing rows; the default is kept afterwards so an INSERT
issued by an older, still-rolling application revision remains valid.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c4a1e8b7d219"
down_revision: Union[str, None] = "385fd6c856b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "submissions",
        sa.Column(
            "parsed_files_text",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("submissions", "parsed_files_text")
