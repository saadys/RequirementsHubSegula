"""
models/db_schemes/requirementshub/schemes/__init__.py
Import all ORM models so Alembic's env.py can detect them
via Base.metadata when running --autogenerate.
"""

from .base import Base  # noqa: F401 — must be first
from .department import Department  # noqa: F401
from .submission import Submission  # noqa: F401
from .fact_extraction import FactExtraction  # noqa: F401
from .scoring_result import ScoringResult  # noqa: F401
from .clarification_round import ClarificationRound  # noqa: F401
from .report import Report  # noqa: F401
from .reviewer_override import ReviewerOverride  # noqa: F401

__all__ = [
    "Base",
    "Department",
    "Submission",
    "FactExtraction",
    "ScoringResult",
    "ClarificationRound",
    "Report",
    "ReviewerOverride",
]
