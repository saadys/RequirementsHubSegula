"""
Corporate & Support Services — Department Prompt (Facade)

Delegates directly to backend.LLM.templates.corporate_support.
"""

from backend.LLM.templates.corporate_support import (
    DEPARTMENT_CONTEXT,
    get_prompt,
)

__all__ = [
    "DEPARTMENT_CONTEXT",
    "get_prompt",
]
