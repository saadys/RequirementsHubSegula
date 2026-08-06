"""
models/SubmissionModel.py
DB operations for the `submissions` table.
Injected into FastAPI routes and LangGraph nodes via AsyncSession dependency.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .BaseDataModel import BaseDataModel, to_uuid
from .db_schemes.requirementshub.schemes.submission import Submission

logger = logging.getLogger("backend.models.submission")


class SubmissionModel(BaseDataModel):

    def __init__(self, db_client: AsyncSession):
        super().__init__(db_client)

    async def create_submission(self, data: dict[str, Any] | Submission) -> Submission:
        """Create a new submission record."""
        if isinstance(data, Submission):
            submission = data
        else:
            submission = Submission(**data)
        return await self.save_and_return(submission)

    async def get_by_id(self, submission_id: str | uuid.UUID) -> Submission | None:
        """Fetch a single submission by UUID (string or UUID object). Returns None if not found."""
        uid = to_uuid(submission_id)
        if not uid:
            logger.warning("Invalid UUID format: %s", submission_id)
            return None

        result = await self.db_client.execute(
            select(Submission).where(Submission.id == uid)
        )
        return result.scalar_one_or_none()

    get_submission_by_id = get_by_id

    async def get_all(
        self,
        status_filter: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Submission]:
        """List submissions with optional status filter, pagination."""
        query = select(Submission).order_by(Submission.created_at.desc())
        if status_filter:
            query = query.where(Submission.status == status_filter)
        query = query.limit(limit).offset(offset)
        result = await self.db_client.execute(query)
        return list(result.scalars().all())

    async def list_submissions(self, status_filter: str | None = None) -> list[Submission]:
        """Alias for get_all."""
        return await self.get_all(status_filter=status_filter)

    async def delete_submission(self, submission_id: str | uuid.UUID) -> bool:
        """Delete a submission by ID."""
        sub = await self.get_by_id(submission_id)
        if sub:
            await self.delete(sub)
            return True
        return False

    async def update_status(self, submission_id: str, status: str) -> Submission | None:
        """Update the status field of a submission. Returns updated instance."""
        submission = await self.get_by_id(submission_id)
        if not submission:
            logger.warning("Submission not found for status update: %s", submission_id)
            return None
        submission.status = status
        await self.db_client.commit()
        await self.db_client.refresh(submission)
        return submission

    async def update_fields(self, submission_id: str, fields: dict[str, Any]) -> Submission | None:
        """Partial update of a submission's fields. Used by clarification nodes."""
        submission = await self.get_by_id(submission_id)
        if not submission:
            return None
        for key, value in fields.items():
            if hasattr(submission, key):
                setattr(submission, key, value)
        await self.db_client.commit()
        await self.db_client.refresh(submission)
        return submission

    async def count_by_status(self) -> dict[str, int]:
        """Returns count of submissions grouped by status. Used by admin dashboard."""
        result = await self.db_client.execute(select(Submission.status))
        statuses = result.scalars().all()
        counts: dict[str, int] = {}
        for s in statuses:
            counts[s] = counts.get(s, 0) + 1
        return counts
