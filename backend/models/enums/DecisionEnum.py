"""
models/enums/DecisionEnum.py
AI pipeline routing decisions.
"""

from enum import Enum


class Decision(str, Enum):
    GO = "GO"
    NO_GO = "NO_GO"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
