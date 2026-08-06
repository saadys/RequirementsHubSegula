"""
models/__init__.py
Clean public API for the models package.
Import models from here for convenient usage in routes and nodes.

Usage:
    from backend.models import SubmissionModel, DepartmentModel, get_db
"""

from .BaseDataModel import BaseDataModel, get_db, AsyncSessionLocal, engine  # noqa: F401
from .SubmissionModel import SubmissionModel  # noqa: F401
from .DepartmentModel import DepartmentModel  # noqa: F401
from .FactExtractionModel import FactExtractionModel  # noqa: F401
from .ScoringModel import ScoringModel  # noqa: F401
from .ClarificationModel import ClarificationModel  # noqa: F401
from .ReportModel import ReportModel  # noqa: F401
from .ReviewerModel import ReviewerModel  # noqa: F401

__all__ = [
    "BaseDataModel",
    "get_db",
    "AsyncSessionLocal",
    "engine",
    "SubmissionModel",
    "DepartmentModel",
    "FactExtractionModel",
    "ScoringModel",
    "ClarificationModel",
    "ReportModel",
    "ReviewerModel",
]
