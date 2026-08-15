"""
Re-export contracts schemas from backend.schemas for backwards compatibility.
"""

from backend.schemas import (
    CategoricalFactExtraction,
    ClarificationQuestions,
    ClarificationQuestionsModel,
    FactExtraction,
    FormSubmission,
    PillarAIViability,
    PillarDataReadiness,
    PillarGovernance,
    PillarIntegration,
    PillarProblemClarity,
    QuestionItem,
    ScoringResult,
)

__all__ = [
    "FactExtraction",
    "CategoricalFactExtraction",
    "PillarAIViability",
    "PillarDataReadiness",
    "PillarProblemClarity",
    "PillarIntegration",
    "PillarGovernance",
    "QuestionItem",
    "ClarificationQuestionsModel",
    "FormSubmission",
    "ScoringResult",
    "ClarificationQuestions",
]
