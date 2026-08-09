"""
Department-specific system prompts for LLM analysis.

Exports base prompt templates and builder functions from backend.LLM.templates.template.
"""

from backend.LLM.templates.template import (
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
