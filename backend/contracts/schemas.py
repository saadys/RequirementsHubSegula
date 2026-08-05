"""
Re-export contracts schemas from backend.schemas for backwards compatibility.
"""

from backend.schemas import (
    ClarificationQuestions,
    FactExtraction,
    FormSubmission,
    ScoringResult,
)

__all__ = [
    "FactExtraction",
    "FormSubmission",
    "ScoringResult",
    "ClarificationQuestions",
]
