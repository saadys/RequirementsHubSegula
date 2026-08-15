"""
models/enums/SubmissionStatusEnum.py
Submission lifecycle statuses.
"""

from enum import Enum


class SubmissionStatus(str, Enum):
    PENDING = "PENDING"
    INCOMPLETE = "INCOMPLETE"
    FAST_TRACK = "FAST_TRACK"
    PROCESSED = "PROCESSED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    IMPLEMENTED = "IMPLEMENTED"
    FAILED = "FAILED"
