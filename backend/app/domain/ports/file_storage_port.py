"""Puerto para almacenamiento seguro de archivos binarios en disco."""
from typing import Protocol


class FileStoragePort(Protocol):
    """Contrato de persistencia privada para archivos FDC cargados."""

    def save(self, content: bytes, extension: str) -> str:
        """Guarda el archivo con nombre seguro y retorna su ruta relativa."""
