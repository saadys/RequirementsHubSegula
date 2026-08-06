"""
models/DepartmentModel.py
DB operations for the `departments` table.
Departments are mostly read-only at runtime (seeded at startup).
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .BaseDataModel import BaseDataModel
from .db_schemes.requirementshub.schemes.department import Department

logger = logging.getLogger("backend.models.department")


class DepartmentModel(BaseDataModel):

    def __init__(self, db_client: AsyncSession):
        super().__init__(db_client)

    async def get_all_enabled(self) -> list[Department]:
        """Returns all departments where enabled=True."""
        result = await self.db_client.execute(
            select(Department).where(Department.enabled == True).order_by(Department.display_name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, department_id: str) -> Department | None:
        """Fetch a department by its slug ID."""
        result = await self.db_client.execute(
            select(Department).where(Department.id == department_id)
        )
        return result.scalar_one_or_none()

    get_department_by_id = get_by_id

    async def get_all_departments(self, enabled_only: bool = True) -> list[Department]:
        """Fetch all departments (optionally enabled only)."""
        if enabled_only:
            return await self.get_all_enabled()
        result = await self.db_client.execute(select(Department).order_by(Department.display_name))
        return list(result.scalars().all())

    async def save_department(self, data: dict | Department) -> Department:
        """Save a department instance or dict."""
        if isinstance(data, Department):
            return await self.save_and_return(data)
        return await self.upsert(data)

    async def upsert(self, data: dict) -> Department:
        """
        Insert or update a department by its slug ID.
        Used during startup seeding from department_configs.json.
        Idempotent: safe to call multiple times.
        """
        existing = await self.get_by_id(data["id"])
        if existing:
            for key, value in data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            await self.db_client.commit()
            await self.db_client.refresh(existing)
            return existing

        department = Department(**data)
        return await self.save_and_return(department)
