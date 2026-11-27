"""Configuración tipada de los Módulos 1 y 2 con pydantic-settings."""
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = APP_DIR.parent


def _parse_model_csv(csv_value: str, primary: str) -> list[str]:
    """Convierte lista separada por comas en lista deduplicada sin el principal."""
    clean_primary = primary.strip()
    seen: set[str] = {clean_primary} if clean_primary else set()
    models: list[str] = []
    for raw in csv_value.split(","):
        candidate = raw.strip()
        if candidate and candidate not in seen:
            seen.add(candidate)
            models.append(candidate)
    return models


class Settings(BaseSettings):
    """Parámetros tipados para persistencia, FDC, sustentación y Google Gemini."""

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
    GEMINI_ANALYSIS_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_DIALOG_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_FALLBACK_MODELS: str = "gemini-3.8-flash"
    GEMINI_TTS_MODEL: str = "gemini-3.8-flash-lite-tts"
    GEMINI_TTS_FALLBACK_MODELS: str = "gemini-2.5-flash-preview-tts"
    GEMINI_TTS_VOICE: str = "Charon"
    TTS_PROVIDER: str = "edge"
    EDGE_TTS_VOICE: str = "es-CO-GonzaloNeural"
    GEMINI_TRANSCRIBE_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_MAX_RETRIES: int = Field(default=1, ge=0)
    GEMINI_RETRY_BASE_DELAY_SECONDS: float = Field(default=1.5, ge=0.0)
    GEMINI_TIMEOUT_SECONDS: int = Field(default=45, ge=5)

    FDC_MAX_UPLOAD_MB: int = 20
    FDC_MIN_TEXT_CHARS: int = 500
    FDC_STORAGE_DIR: Path = BACKEND_DIR / "storage"
    RUBRICS_DIR: Path = APP_DIR / "data"

    DEFENSE_MAX_AUDIO_MB: int = 20
    DEFENSE_MIN_WORDS: int = 4

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
    def gemini_fallback_models(self) -> list[str]:
        """Modelos de respaldo para análisis FDC."""
        return _parse_model_csv(self.GEMINI_FALLBACK_MODELS, self.GEMINI_ANALYSIS_MODEL)

    @property
    def gemini_dialog_fallback_models(self) -> list[str]:
        """Modelos de respaldo para generación de preguntas y evaluación oral."""
        return _parse_model_csv(self.GEMINI_FALLBACK_MODELS, self.GEMINI_DIALOG_MODEL)

    @property
    def gemini_tts_fallback_models(self) -> list[str]:
        """Modelos de respaldo para síntesis de voz neuronal (TTS)."""
        return _parse_model_csv(self.GEMINI_TTS_FALLBACK_MODELS, self.GEMINI_TTS_MODEL)

    @property
    def gemini_transcribe_fallback_models(self) -> list[str]:
        """Modelos de respaldo para transcripción multimodal de audio (STT)."""
        return _parse_model_csv(self.GEMINI_FALLBACK_MODELS, self.GEMINI_TRANSCRIBE_MODEL)

    @property
    def fdc_max_upload_bytes(self) -> int:
        """Límite máximo de carga FDC en bytes."""
        return self.FDC_MAX_UPLOAD_MB * 1024 * 1024

    @property
    def defense_max_audio_bytes(self) -> int:
        """Límite máximo de carga de audio en bytes."""
        return self.DEFENSE_MAX_AUDIO_MB * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna instancia cacheada de configuración."""
    return Settings()
