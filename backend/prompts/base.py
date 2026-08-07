"""
Base Prompt Components (Re-exported from LLM Templates)

Shared system prompt structure used across all department prompts.
Delegates to backend.LLM.templates.template.
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
