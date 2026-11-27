"""Fábrica de registro de los Módulos 1 y 2 en la aplicación FastAPI."""
from fastapi import FastAPI

from app.core.container import Container
from app.core.settings import get_settings
from app.presentation.api.v1.routers.defense_router import router as defense_router
from app.presentation.api.v1.routers.fdc_router import router as fdc_router
from app.presentation.error_handlers import register_exception_handlers


def register_fdc_module(app: FastAPI, container: Container | None = None) -> None:
    """Inicializa contenedor, esquema DB opcional, rutas v1 y error handlers."""
    resolved = container or Container(get_settings())
    if resolved.settings.DB_AUTO_CREATE:
        resolved.init_db()
    app.state.container = resolved
    app.include_router(fdc_router, prefix="/api/v1")
    app.include_router(defense_router, prefix="/api/v1")
    register_exception_handlers(app)
