"""Prueba de migración Alembic 0001 upgrade/downgrade sobre SQLite."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.settings import get_settings


def test_alembic_upgrade_and_downgrade(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "alembic_test.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    get_settings.cache_clear()

    backend_dir = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    try:
        command.upgrade(cfg, "head")
        engine = create_engine(db_url)
        tables = set(inspect(engine).get_table_names())
        assert {"projects", "fdc_documents", "fdc_analyses"}.issubset(tables)
        engine.dispose()

        command.downgrade(cfg, "base")
        engine_after = create_engine(db_url)
        tables_after = set(inspect(engine_after).get_table_names())
        assert not {"projects", "fdc_documents", "fdc_analyses"} & tables_after
        engine_after.dispose()
    finally:
        get_settings.cache_clear()
