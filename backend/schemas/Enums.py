"""
Enums for the AI Requirement Hub.
Defines domain constants and status types.
"""

from enum import Enum


class SubmissionStatus(str, Enum):
    PROCESSED = "PROCESSED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    INCOMPLETE = "INCOMPLETE"
    FAST_TRACK = "FAST_TRACK"
    PENDING = "PENDING"


class Decision(str, Enum):
    GO = "GO"
    NO_GO = "NO_GO"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


class DeadlineUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProblemCategory(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    TIME_SERIES = "time_series"
    RECOMMENDATION = "recommendation"
    OPTIMIZATION = "optimization"
    GENERATIVE = "generative"
    OTHER = "other"
    UNKNOWN = "unknown"
