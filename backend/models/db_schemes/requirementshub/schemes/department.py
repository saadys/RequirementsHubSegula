"""
models/db_schemes/requirementshub/schemes/department.py
ORM model for the `departments` table.
Stores available business departments and their configuration.
"""

import uuid
from sqlalchemy import String, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

JSON_TYPE = JSONB().with_variant(JSON, "sqlite")


class Department(Base):
    __tablename__ = "departments"

    # Primary Key: human-readable slug (e.g., 'corporate_support', 'automotive')
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # JSONB: dynamic field configuration specific to this department
    # Example: [{"name": "vehicle_type", "label": "Type de véhicule", "type": "select", ...}]
    specific_fields: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=list)

    # Relationships
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="department_rel", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Department id={self.id} display_name={self.display_name!r}>"
