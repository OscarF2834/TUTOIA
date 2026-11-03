"""
Tutoia · Configuración central.

Toda la configuración vive en variables de entorno (cargadas desde
``backend/.env``) para que la plataforma sea desplegable en cualquier
entorno —portátil del estudiante, servidor de la universidad o la nube—
sin cambiar una sola línea de código.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent          # backend/app
BACKEND_DIR = BASE_DIR.parent                        # backend
PROJECT_ROOT = BACKEND_DIR.parent                    # raíz del repositorio

load_dotenv(BACKEND_DIR / ".env")


class Settings:
    """Parámetros de ejecución de la plataforma."""

    # ── Rutas raíz ─────────────────────────────────────────────────
    BACKEND_DIR: Path = BACKEND_DIR
    PROJECT_ROOT: Path = PROJECT_ROOT

    # ── Aplicación ─────────────────────────────────────────────────
    APP_NAME: str = "Tutoia"
    VERSION: str = "0.1.0"

    # ── Motor de inteligencia ──────────────────────────────────────
    # mock  → motor heurístico local (determinista, sin red).
    # live  → LLM en la nube (juicio semántico completo, requiere API key).
    LLM_MODE: str = os.getenv("LLM_MODE", "mock").strip().lower()
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "").strip()
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip()
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.4"))

    # ── Almacenamiento runtime ─────────────────────────────────────
    RUBRICAS_DIR: Path = BASE_DIR / "data"
    STORAGE_DIR: Path = BASE_DIR / "storage"
    SESIONES_DIR: Path = STORAGE_DIR / "sesiones"
    REPORTES_DIR: Path = STORAGE_DIR / "actas"

    # ── Límites de la sustentación ─────────────────────────────────
    MAX_INTERACCIONES: int = 14          # techo de seguridad anti-bucle
    MIN_RESPUESTA_PALABRAS: int = 4      # umbral para pedir reformulación


settings = Settings()

# Directorios de trabajo creados en caliente (idempotente).
for _dir in (settings.STORAGE_DIR, settings.SESIONES_DIR, settings.REPORTES_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
