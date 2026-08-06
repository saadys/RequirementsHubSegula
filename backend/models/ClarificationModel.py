"""
models/ClarificationModel.py
DB operations for the `clarification_rounds` table.
1:N relationship — a submission can have multiple clarification rounds (max = MAX_CLARIFICATION_ROUNDS).
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .BaseDataModel import BaseDataModel, to_uuid
from .db_schemes.requirementshub.schemes.clarification_round import ClarificationRound

logger = logging.getLogger("backend.models.clarification")


class ClarificationModel(BaseDataModel):

    def __init__(self, db_client: AsyncSession):
        super().__init__(db_client)

    async def create_round(
        self,
        submission_id: str | uuid.UUID,
        round_number: int,
        questions: list[str],
        answers: list[str] | None = None,
    ) -> ClarificationRound:
        """Create a new clarification round for a submission."""
        uid = to_uuid(submission_id)
        if not uid:
            raise ValueError(f"Invalid UUID: {submission_id}")
        round_ = ClarificationRound(
            submission_id=uid,
            round_number=round_number,
            questions=questions,
            answers=answers or [],
        )
        return await self.save_and_return(round_)

    async def update_answers(
        self, submission_id: str | uuid.UUID, round_number: int, answers: list[str]
    ) -> ClarificationRound | None:
        """Record user answers for a specific clarification round."""
        uid = to_uuid(submission_id)
        if not uid:
            return None
        result = await self.db_client.execute(
            select(ClarificationRound).where(
                ClarificationRound.submission_id == uid,
                ClarificationRound.round_number == round_number,
            )
        )
        round_ = result.scalar_one_or_none()
        if not round_:
            logger.warning(
                "ClarificationRound not found: submission=%s round=%s",
                submission_id,
                round_number,
            )
            return None
        round_.answers = answers
        await self.db_client.commit()
        await self.db_client.refresh(round_)
        return round_

    async def save_clarification_round(self, round_obj: ClarificationRound) -> ClarificationRound:
        """Save a ClarificationRound ORM instance."""
        return await self.save_and_return(round_obj)

    async def get_rounds_for_submission(
        self, submission_id: str | uuid.UUID
    ) -> list[ClarificationRound]:
        """Returns all clarification rounds for a submission, ordered by round number."""
        uid = to_uuid(submission_id)
        if not uid:
            return []
        result = await self.db_client.execute(
            select(ClarificationRound)
            .where(ClarificationRound.submission_id == uid)
            .order_by(ClarificationRound.round_number)
        )
        return list(result.scalars().all())

    get_rounds_by_submission_id = get_rounds_for_submission

    async def get_latest_round(self, submission_id: str | uuid.UUID) -> ClarificationRound | None:
        """Returns the most recent clarification round for a submission."""
        rounds = await self.get_rounds_for_submission(submission_id)
        return rounds[-1] if rounds else None

    async def count_rounds(self, submission_id: str | uuid.UUID) -> int:
        """Returns the number of clarification rounds already completed."""
        rounds = await self.get_rounds_for_submission(submission_id)
        return len(rounds)
