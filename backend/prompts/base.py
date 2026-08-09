"""
Base Prompt Components (Facade)

Delegates to backend.prompts.__init__ for backward compatibility.
"""

from backend.prompts import (
    SYSTEM_ROLE,
    EXTRACTION_RULES,
    CLARIFICATION_CONTEXT,
    RAG_CONTEXT,
    build_system_prompt,
)

__all__ = [
    "SYSTEM_ROLE",
    "EXTRACTION_RULES",
    "CLARIFICATION_CONTEXT",
    "RAG_CONTEXT",
    "build_system_prompt",
]
