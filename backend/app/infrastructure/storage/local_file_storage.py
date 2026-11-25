"""Almacenamiento privado seguro para archivos FDC en disco local."""
from pathlib import Path
from uuid import uuid4


class LocalFileStorage:
    """Guarda binarios en `storage_dir/fdc_uploads/{uuid}{ext}` validando path traversal."""

    def __init__(self, storage_dir: Path) -> None:
        self._base_dir = storage_dir.resolve()
        self._uploads_dir = (self._base_dir / "fdc_uploads").resolve()
        self._uploads_dir.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, extension: str) -> str:
        """Persiste el binario y retorna su ruta relativa dentro del storage."""
        clean_ext = extension if extension.startswith(".") else f".{extension}"
        filename = f"{uuid4().hex}{clean_ext.lower()}"
        target = (self._uploads_dir / filename).resolve()
        if not target.is_relative_to(self._uploads_dir):
            raise ValueError("Ruta de almacenamiento inválida fuera del directorio base.")
        target.write_bytes(content)
        return f"fdc_uploads/{filename}"
