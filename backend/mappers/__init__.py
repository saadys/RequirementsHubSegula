"""Mapper layer — ORM entities to API DTOs.

Isolates persistence-shaped data from wire-shaped data so routes stay thin and
the projection rules (which questions are still actionable, where the effective
decision comes from, how a scoring breakdown is flattened) live in exactly one
place instead of being re-derived per endpoint.
"""

from backend.mappers.submission_mapper import (
    ClarificationView,
    build_clarification_response,
    build_submission_response,
    project_clarification_view,
)

__all__ = [
    "ClarificationView",
    "build_clarification_response",
    "build_submission_response",
    "project_clarification_view",
]
