"""
LLM Framework Enums

Defines standard enums for LLM providers, models, and conversation roles.
"""

from enum import Enum


class LLMProviderEnum(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    MISTRAL = "mistral"
    FALLBACK = "fallback"
    LOCAL = "local"


class LLMModelEnum(str, Enum):
    GEMINI_PRIMARY = "gemini-3.1-flash-lite"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    QWEN3_8B = "ollama/qwen3:8b"
    QWEN_7B = "ollama/qwen2.5:7b-instruct"


class LLMRoleEnum(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
