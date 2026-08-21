"""
Base LLM Provider

Provides shared logging and helper functions for concrete LLM providers.
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from backend.LLM.LLMInterfaces import LLMInterface, T


class BaseLLMProvider(LLMInterface):
    """Base class with shared provider functionality."""

    def __init__(self, model_name: str, temperature: float = 0.0):
        self.model_name = model_name
        self.default_temperature = temperature
        self.logger = logging.getLogger(self.__class__.__name__)
        # Set after each generate_* call to the model that actually served the
        # request (may differ from model_name after a key/provider fallback).
        self.last_model_used: Optional[str] = None

    def _format_messages(
        self,
        prompt: str | List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Formats string or list of dicts into standard message list."""
        messages: List[Dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if isinstance(prompt, str):
            messages.append({"role": "user", "content": prompt})
        elif isinstance(prompt, list):
            for msg in prompt:
                messages.append({"role": msg["role"], "content": msg["content"]})

        return messages
