"""Base declarativa SQLAlchemy 2.0 y tipo JSON compatible PostgreSQL/SQLite."""
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


JsonVariant = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    """Clase base para los modelos ORM de TutoIA."""
