"""
LLM Error Classification

Distinguishes failures worth routing to a different provider from failures that
would fail identically there.

A blanket `except Exception` around a fallback is a latency and cost
amplifier: a malformed prompt (400), an exhausted schema-validation loop, or a
context-length overflow will fail on the secondary provider too, so retrying
them merely doubles the bill and the wait before surfacing the same error.
Only availability failures — the remote side being unreachable, overloaded,
asleep, or rate-limited — justify switching providers.
"""

import asyncio
import logging
from typing import Tuple

import httpx
import litellm
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def _litellm_exc(*names: str) -> Tuple[type, ...]:
    """Resolves litellm exception classes defensively across versions."""
    resolved = []
    for name in names:
        cls = getattr(litellm, name, None)
        if isinstance(cls, type) and issubclass(cls, BaseException):
            resolved.append(cls)
    return tuple(resolved)


# Availability failures: the request never got a usable answer from the remote
# side. A different provider has a genuine chance of succeeding.
TRANSIENT_EXCEPTIONS: Tuple[type, ...] = (
    asyncio.TimeoutError,
    ConnectionError,
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.ReadError,
    httpx.RemoteProtocolError,
) + _litellm_exc(
    "Timeout",
    "APIConnectionError",
    "APIError",
    "InternalServerError",
    "ServiceUnavailableError",
    "RateLimitError",
)

# Deterministic failures: the same input will fail the same way elsewhere.
# Checked first, because litellm's hierarchy makes some of these subclasses of
# the broad APIError above.
PERMANENT_EXCEPTIONS: Tuple[type, ...] = (
    ValidationError,
    ValueError,          # includes json.JSONDecodeError
    TypeError,
    KeyError,
) + _litellm_exc(
    "BadRequestError",
    "ContextWindowExceededError",
    "UnsupportedParamsError",
)

# Auth failures are provider-scoped: a bad vLLM token says nothing about the
# Gemini key, so they are worth a fallback even though they are not transient.
AUTH_EXCEPTIONS: Tuple[type, ...] = _litellm_exc(
    "AuthenticationError",
    "PermissionDeniedError",
)

_TRANSIENT_STATUS = frozenset({408, 429, 500, 502, 503, 504, 522, 524})
_PERMANENT_STATUS = frozenset({400, 404, 405, 413, 422})


def is_retryable(exc: BaseException) -> bool:
    """True when routing this failure to another provider is worthwhile.

    Ordering matters: a specific permanent class is checked before the broader
    transient ones, and an explicit HTTP status wins over class membership
    because litellm wraps several distinct conditions in one exception type.
    """
    status = getattr(exc, "status_code", None)
    if status is None:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)

    if isinstance(status, int):
        if status in _PERMANENT_STATUS:
            return False
        if status in _TRANSIENT_STATUS or status >= 500:
            return True

    if isinstance(exc, AUTH_EXCEPTIONS):
        return True
    if isinstance(exc, PERMANENT_EXCEPTIONS):
        return False
    if isinstance(exc, TRANSIENT_EXCEPTIONS):
        return True

    # Unknown failures are treated as retryable: an unnecessary fallback costs
    # one extra call, whereas a missed one takes down a user-facing request.
    logger.debug("Unclassified LLM exception %s treated as retryable", type(exc).__name__)
    return True


def describe(exc: BaseException) -> str:
    """Compact log-friendly description of a provider failure."""
    status = getattr(exc, "status_code", None)
    suffix = f" status={status}" if status is not None else ""
    return f"{type(exc).__name__}{suffix}: {exc}"
