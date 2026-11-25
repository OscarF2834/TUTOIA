"""Configuración tipada del Módulo 1 con pydantic-settings."""
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = APP_DIR.parent


class Settings(BaseSettings):
    """Parámetros tipados para persistencia, ingesta FDC y Google Gemini."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "TutoIA"
    VERSION: str = "1.0.0"

    DATABASE_URL: str = "sqlite:///./tutoia_dev.db"
    DB_AUTO_CREATE: bool = True

    GEMINI_API_KEY: str = ""
    GEMINI_ANALYSIS_MODEL: str = "gemini-3.8-flash"
    GEMINI_DIALOG_MODEL: str = "gemini-3.8-flash"
    GEMINI_TIMEOUT_SECONDS: int = 120

    FDC_MAX_UPLOAD_MB: int = 20
    FDC_MIN_TEXT_CHARS: int = 500
    FDC_STORAGE_DIR: Path = BACKEND_DIR / "storage"

    @field_validator("DATABASE_URL")
    @classmethod
    def _resolve_relative_sqlite_url(cls, value: str) -> str:
        prefix = "sqlite:///./"
        if value.startswith(prefix):
            rel_path = value[len(prefix):]
            abs_path = (BACKEND_DIR / rel_path).resolve()
            return f"sqlite:///{abs_path.as_posix()}"
        return value

    @property
    def fdc_max_upload_bytes(self) -> int:
        """Límite máximo de carga en bytes."""
        return self.FDC_MAX_UPLOAD_MB * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna instancia cacheada de configuración."""
    return Settings()
