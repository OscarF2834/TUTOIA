"""Clase base abstracta del patrón Chain of Responsibility."""
from abc import ABC, abstractmethod

from app.application.dto.fdc_ingestion_dto import FdcIngestionContext


class IngestionHandler(ABC):
    """Eslabón base encadenable para la validación e ingesta FDC."""

    def __init__(self) -> None:
        self._next: IngestionHandler | None = None

    def set_next(self, handler: "IngestionHandler") -> "IngestionHandler":
        """Enlaza el siguiente eslabón y lo retorna para encadenamiento fluido."""
        self._next = handler
        return handler

    def handle(self, ctx: FdcIngestionContext) -> FdcIngestionContext:
        """Ejecuta el eslabón actual y delega al siguiente si existe."""
        self._process(ctx)
        if self._next is not None:
            return self._next.handle(ctx)
        return ctx

    @abstractmethod
    def _process(self, ctx: FdcIngestionContext) -> None:
        """Ejecuta la validación o transformación propia del eslabón."""
