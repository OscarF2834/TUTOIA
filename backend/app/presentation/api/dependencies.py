"""Dependencias FastAPI para sesiones DB y fachadas."""
from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.application.facades.fdc_ingestion_facade import FdcIngestionFacade
from app.core.container import Container


def get_container(request: Request) -> Container:
    """Obtiene el contenedor desde app.state."""
    return request.app.state.container


def get_db_session(
    container: Container = Depends(get_container),
) -> Generator[Session, None, None]:
    """Abre y cierra una sesión SQLAlchemy por petición HTTP."""
    session = container.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_fdc_facade(
    container: Container = Depends(get_container),
    session: Session = Depends(get_db_session),
) -> FdcIngestionFacade:
    """Provee FdcIngestionFacade acoplada a la sesión de la petición."""
    return container.fdc_facade(session)
