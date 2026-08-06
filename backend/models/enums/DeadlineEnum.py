"""
models/enums/DeadlineEnum.py
Deadline urgency levels for submissions.
"""

from enum import Enum


class DeadlineUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
