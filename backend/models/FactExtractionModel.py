"""
models/FactExtractionModel.py
DB operations for the `fact_extractions` table.
Written by the LLM analyze node. Read by the scoring node and admin dashboard.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from .BaseDataModel import BaseDataModel, to_uuid
from .db_schemes.requirementshub.schemes.fact_extraction import FactExtraction

logger = logging.getLogger("backend.models.fact_extraction")


class FactExtractionModel(BaseDataModel):

    def __init__(self, db_client: AsyncSession):
        super().__init__(db_client)

    def _normalize_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalizes 5-pillar extraction data or legacy data into flat ORM fields."""
        normalized = {}

        # If data is in 5-pillar categorical format:
        if "ai_viability" in data and isinstance(data["ai_viability"], dict):
            normalized["ai_viability_category"] = data["ai_viability"].get("category")
            normalized["ai_viability_reason"] = data["ai_viability"].get("reason")
        if "data_readiness" in data and isinstance(data["data_readiness"], dict):
            normalized["data_readiness_category"] = data["data_readiness"].get("category")
            normalized["data_readiness_reason"] = data["data_readiness"].get("reason")
        if "problem_clarity" in data and isinstance(data["problem_clarity"], dict):
            normalized["problem_clarity_category"] = data["problem_clarity"].get("category")
            normalized["problem_clarity_reason"] = data["problem_clarity"].get("reason")
        if "integration_feasibility" in data and isinstance(data["integration_feasibility"], dict):
            normalized["integration_category"] = data["integration_feasibility"].get("category")
            normalized["integration_reason"] = data["integration_feasibility"].get("reason")
        if "governance_and_safety" in data and isinstance(data["governance_and_safety"], dict):
            normalized["governance_category"] = data["governance_and_safety"].get("category")
            normalized["governance_reason"] = data["governance_and_safety"].get("reason")

        if "identified_technique" in data:
            normalized["identified_technique"] = data["identified_technique"]
            normalized["ai_technique_identified"] = data["identified_technique"]
        if "project_summary" in data:
            normalized["project_summary"] = data["project_summary"]
            normalized["summary"] = data["project_summary"]

        # Preserve entire raw dictionary
        normalized["raw_extraction"] = data

        # Copy any other direct scalar/list fields
        for k, v in data.items():
            if k not in ["ai_viability", "data_readiness", "problem_clarity", "integration_feasibility", "governance_and_safety"]:
                normalized[k] = v

        return normalized

    async def create_or_update(
        self, submission_id: str | uuid.UUID, data: dict[str, Any], auto_commit: bool = True
    ) -> FactExtraction:
        """
        Upsert fact extraction for a submission.
        Uses PostgreSQL ON CONFLICT for idempotent pipeline re-runs.
        If the LLM pipeline reruns (e.g., after clarification), the existing
        row is updated rather than creating a duplicate.
        """
        uid = to_uuid(submission_id)
        if not uid:
            raise ValueError(f"Invalid UUID: {submission_id}")
        
        flat_data = self._normalize_data(data)
        existing = await self.get_by_submission_id(uid)

        if existing:
            for key, value in flat_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            if auto_commit:
                await self.db_client.commit()
                await self.db_client.refresh(existing)
            else:
                await self.db_client.flush()
            logger.info("FactExtraction updated for submission %s", submission_id)
            return existing

        # Filter fields that exist on FactExtraction model
        valid_fields = {k: v for k, v in flat_data.items() if hasattr(FactExtraction, k)}
        fact = FactExtraction(submission_id=uid, **valid_fields)
        return await self.save_and_return(fact, auto_commit=auto_commit)

    async def save_fact_extraction(self, fact: FactExtraction, auto_commit: bool = True) -> FactExtraction:
        """Save a FactExtraction ORM instance."""
        if isinstance(fact, FactExtraction):
            return await self.save_and_return(fact, auto_commit=auto_commit)
        return await self.create_or_update(fact["submission_id"], fact, auto_commit=auto_commit)

    async def get_by_submission_id(self, submission_id: str | uuid.UUID) -> FactExtraction | None:
        """Fetch fact extraction by submission UUID."""
        uid = to_uuid(submission_id)
        if not uid:
            return None
        result = await self.db_client.execute(
            select(FactExtraction).where(FactExtraction.submission_id == uid)
        )
        return result.scalar_one_or_none()
