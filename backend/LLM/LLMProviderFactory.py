"""
LLM Provider Factory

Factory responsible for instantiating LLM providers and wiring the failover
pipeline, driven by declarative configuration (LLM_BACKEND /
LLM_FALLBACK_BACKEND) rather than branching logic scattered across callers.

Adding a backend means adding one builder to _BUILDERS; no call site changes.
"""

import logging
from typing import Callable, Dict, Optional

from backend import config
from backend.LLM.LLMEnums import LLMProviderEnum
from backend.LLM.LLMInterfaces import LLMInterface
from backend.LLM.providers.fallback_provider import FallbackLLMProvider
from backend.LLM.providers.GeminiProvider import GeminiProvider
from backend.LLM.providers.LocalLLM import LocalLLMProvider
from backend.LLM.providers.openai_compat_provider import OpenAICompatProvider
from backend.LLM.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

# Legacy enum values map onto the named backends so existing callers passing
# provider_type= keep working unchanged.
_ENUM_TO_BACKEND: Dict[LLMProviderEnum, str] = {
    LLMProviderEnum.LOCAL: config.BACKEND_OLLAMA_LOCAL,
    LLMProviderEnum.VLLM: config.BACKEND_LIGHTNING_VLLM,
    LLMProviderEnum.GEMINI: config.BACKEND_GEMINI_CLOUD,
    LLMProviderEnum.OPENAI: config.BACKEND_OPENAI_CLOUD,
}


def _build_ollama_local(model_name: Optional[str], temperature: float) -> LLMInterface:
    return LocalLLMProvider(
        model_name=model_name or config.OLLAMA_MODEL,
        temperature=temperature,
        api_base=config.OLLAMA_BASE_URL,
    )


def _build_lightning_vllm(model_name: Optional[str], temperature: float) -> LLMInterface:
    return OpenAICompatProvider(
        model_name=model_name or config.VLLM_MODEL,
        temperature=temperature,
        api_base=config.VLLM_BASE_URL,
        api_key=config.VLLM_API_KEY,
    )


def _build_gemini_cloud(model_name: Optional[str], temperature: float) -> LLMInterface:
    return GeminiProvider(
        model_name=model_name or config.PRIMARY_MODEL,
        temperature=temperature,
    )


def _build_openai_cloud(model_name: Optional[str], temperature: float) -> LLMInterface:
    return OpenAIProvider(
        model_name=model_name or config.FALLBACK_MODEL,
        temperature=temperature,
    )


_BUILDERS: Dict[str, Callable[[Optional[str], float], LLMInterface]] = {
    config.BACKEND_OLLAMA_LOCAL: _build_ollama_local,
    config.BACKEND_LIGHTNING_VLLM: _build_lightning_vllm,
    config.BACKEND_GEMINI_CLOUD: _build_gemini_cloud,
    config.BACKEND_OPENAI_CLOUD: _build_openai_cloud,
}


class LLMProviderFactory:
    """Factory for creating LLM Provider instances."""

    @staticmethod
    def build_backend(
        backend: str,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
    ) -> LLMInterface:
        """Instantiates a single bare provider for `backend`, without fallback."""
        builder = _BUILDERS.get(backend)
        if builder is None:
            raise ValueError(
                f"Unknown LLM backend '{backend}'. "
                f"Expected one of: {', '.join(sorted(_BUILDERS))}."
            )
        return builder(model_name, temperature)

    @staticmethod
    def _build_fallback(temperature: float) -> Optional[LLMInterface]:
        """Builds the secondary provider, or None when unavailable/disabled."""
        backend = config.LLM_FALLBACK_BACKEND

        if backend in (config.BACKEND_NONE, "", config.LLM_BACKEND):
            # Falling back to the same backend buys nothing: if it is down for
            # the primary call, it is down for the retry too.
            return None

        # A cloud fallback without credentials is worse than none: it turns an
        # availability error into a confusing auth error.
        if backend == config.BACKEND_GEMINI_CLOUD and not (
            config.GEMINI_API_KEY_1 or config.GEMINI_API_KEY_2
        ):
            logger.warning("Fallback backend 'gemini_cloud' has no API key configured; disabled.")
            return None
        if backend == config.BACKEND_OPENAI_CLOUD and not config.OPENAI_API_KEY:
            logger.warning("Fallback backend 'openai_cloud' has no API key configured; disabled.")
            return None

        try:
            return LLMProviderFactory.build_backend(backend, temperature=temperature)
        except Exception as exc:
            logger.error("Failed to build fallback backend '%s': %s", backend, exc)
            return None

    @staticmethod
    def get_provider(
        provider_type: Optional[LLMProviderEnum] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        backend: Optional[str] = None,
        with_fallback: bool = True,
    ) -> LLMInterface:
        """Returns a configured provider, wrapped in the failover decorator.

        Resolution order: explicit `backend` > legacy `provider_type` enum >
        config.LLM_BACKEND. Passing an explicit target implies a deliberate
        choice, so no fallback is attached in that case.
        """
        if backend is None and provider_type is not None:
            backend = _ENUM_TO_BACKEND.get(provider_type)
            if backend is None:
                raise ValueError(f"Provider type '{provider_type}' has no registered backend.")

        if backend is not None:
            # Explicit target: honour it exactly, no silent rerouting.
            return LLMProviderFactory.build_backend(backend, model_name, temperature)

        primary = LLMProviderFactory.build_backend(
            config.LLM_BACKEND, model_name, temperature
        )
        if not with_fallback:
            return primary

        fallback = LLMProviderFactory._build_fallback(temperature)
        logger.info(
            "LLM pipeline initialised | primary=%s (%s) fallback=%s",
            config.LLM_BACKEND,
            getattr(primary, "model_name", "?"),
            getattr(fallback, "model_name", None) if fallback else "disabled",
        )
        return FallbackLLMProvider(primary_provider=primary, fallback_provider=fallback)
