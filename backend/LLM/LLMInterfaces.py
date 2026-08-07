"""
LLM Framework Interfaces

Defines the abstract contract (LLMInterface) that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMInterface(ABC):
    """Abstract Base Class for LLM Providers."""

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generates standard un-structured text response from the LLM."""
        pass

    @abstractmethod
    def generate_structured_output(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        """Generates structured output validated against a Pydantic schema."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Checks if the provider is configured and accessible."""
        pass
