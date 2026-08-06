"""
models/db_schemes/requirementshub/schemes/base.py
SQLAlchemy 2.0 DeclarativeBase — single source of truth for all ORM models.
All table classes in this package inherit from this Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
