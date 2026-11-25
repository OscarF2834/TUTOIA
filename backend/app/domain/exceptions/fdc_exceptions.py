"""Excepciones semánticas del dominio de ingesta y análisis FDC."""
from typing import Any


class FdcDomainError(Exception):
    """Excepción base del dominio FDC con código estable y contexto."""

    def __init__(
        self,
        message: str,
        code: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}


class EmptyDocumentError(FdcDomainError):
    """El archivo cargado está vacío (0 bytes)."""

    def __init__(self, message: str = "El archivo cargado está vacío.", context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="FDC_EMPTY_FILE", context=context)


class FileTooLargeError(FdcDomainError):
    """El archivo supera el tamaño máximo institucional permitido."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="FDC_FILE_TOO_LARGE", context=context)


class UnsupportedDocumentFormatError(FdcDomainError):
    """Extensión o firma binaria incompatible con PDF o DOCX."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="FDC_UNSUPPORTED_FORMAT", context=context)


class CorruptedDocumentError(FdcDomainError):
    """El binario PDF o DOCX está dañado y no puede abrirse."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="FDC_CORRUPTED_FILE", context=context)


class UnreadableDocumentError(FdcDomainError):
    """Documento cifrado, escaneado sin texto o con contenido insuficiente."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="FDC_UNREADABLE", context=context)


class InvalidFdcStructureError(FdcDomainError):
    """El texto no contiene las secciones mínimas exigidas para el FDC."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="FDC_INVALID_STRUCTURE", context=context)


class UnsupportedFdcTypeError(FdcDomainError):
    """El código de formato FDC solicitado no está registrado."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="FDC_UNSUPPORTED_TYPE", context=context)


class FdcDocumentNotFoundError(FdcDomainError):
    """No existe un documento FDC para el identificador consultado."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="FDC_DOCUMENT_NOT_FOUND", context=context)


class AiProviderNotConfiguredError(FdcDomainError):
    """Falta la clave o configuración del proveedor de IA."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="AI_PROVIDER_NOT_CONFIGURED", context=context)


class AiProviderUnavailableError(FdcDomainError):
    """Fallo de conectividad o respuesta anómala del proveedor de IA."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="AI_PROVIDER_UNAVAILABLE", context=context)


class AiResponseValidationError(FdcDomainError):
    """La salida del modelo IA no cumplió el esquema estructurado esperado."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="AI_RESPONSE_VALIDATION_ERROR", context=context)
