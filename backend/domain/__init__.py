"""Domain layer — pure business rules, free of I/O, ORM and framework concerns.

Everything here is synchronous, side-effect free and unit-testable without a
database, an HTTP client or an event loop. If a module in this package ever needs
an `await`, a `Session` or a `Request`, it belongs in `services/` instead.
"""

from backend.domain.status_policy import resolve_submission_status

__all__ = ["resolve_submission_status"]
