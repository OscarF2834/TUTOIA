"""Fábrica de Engine SQLAlchemy 2.0 compatible con PostgreSQL y SQLite."""
from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import StaticPool


def build_engine(database_url: str) -> Engine:
    """Construye el Engine SQLAlchemy según el dialecto configurado."""
    if database_url.startswith("sqlite"):
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in database_url:
            kwargs["poolclass"] = StaticPool
        return create_engine(database_url, **kwargs)
    return create_engine(database_url, pool_pre_ping=True)
