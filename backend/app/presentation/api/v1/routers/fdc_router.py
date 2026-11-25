"""Router HTTP v1 para ingesta y consulta de documentos FDC."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from starlette.concurrency import run_in_threadpool

from app.application.dto.fdc_ingestion_dto import FdcUploadCommand
from app.application.facades.fdc_ingestion_facade import FdcIngestionFacade
from app.core.container import Container
from app.domain.entities.fdc_document import FdcType, Modality
from app.presentation.api.dependencies import get_container, get_fdc_facade
from app.presentation.api.v1.schemas.fdc_http_schemas import (
    ErrorResponseSchema,
    FdcDocumentResponseSchema,
)

router = APIRouter(prefix="/fdc", tags=["Módulo 1 · FDC"])

_ERROR_RESPONSES = {
    413: {"model": ErrorResponseSchema, "description": "Archivo excede tamaño máximo permitido."},
    415: {"model": ErrorResponseSchema, "description": "Extensión o formato binario no soportado."},
    422: {"model": ErrorResponseSchema, "description": "Archivo vacío, ilegible o sin estructura FDC."},
    502: {"model": ErrorResponseSchema, "description": "Fallo de comunicación o esquema con Gemini."},
    503: {"model": ErrorResponseSchema, "description": "GEMINI_API_KEY no configurada."},
}


@router.post(
    "/upload",
    response_model=FdcDocumentResponseSchema,
    status_code=201,
    responses=_ERROR_RESPONSES,
    summary="Cargar y analizar documento F-DC-124 o F-DC-125",
)
async def upload_fdc_document(
    file: UploadFile = File(...),
    fdc_type: Literal["FDC_124", "FDC_125"] = Form("FDC_125"),
    academic_program: str | None = Form(None),
    modality: Literal[
        "DESARROLLO_TECNOLOGICO",
        "INVESTIGACION",
        "MONOGRAFIA",
        "EMPRENDIMIENTO",
    ] | None = Form(None),
    container: Container = Depends(get_container),
    facade: FdcIngestionFacade = Depends(get_fdc_facade),
) -> FdcDocumentResponseSchema:
    """Valida, indexa en Gemini Files API y analiza un documento FDC."""
    max_bytes = container.settings.fdc_max_upload_bytes
    content = await file.read(max_bytes + 1)
    cmd = FdcUploadCommand(
        filename=file.filename or "documento",
        content=content,
        fdc_type=FdcType(fdc_type),
        academic_program=academic_program,
        modality=Modality(modality) if modality else None,
    )
    view = await run_in_threadpool(facade.upload, cmd)
    return FdcDocumentResponseSchema.from_view(view)


@router.get(
    "/{document_id}",
    response_model=FdcDocumentResponseSchema,
    responses={404: {"model": ErrorResponseSchema, "description": "Documento FDC no encontrado."}},
    summary="Consultar diagnóstico de documento FDC",
)
def get_fdc_document(
    document_id: UUID,
    facade: FdcIngestionFacade = Depends(get_fdc_facade),
) -> FdcDocumentResponseSchema:
    """Retorna el proyecto, documento y análisis estructurado persistido."""
    view = facade.get(document_id)
    return FdcDocumentResponseSchema.from_view(view)
