"""Router HTTP v1 para sustentación oral con AURA y actas oficiales (Módulos 2 y 3A)."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, Query, UploadFile
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

from app.application.dto.defense_dtos import (
    CreateDefenseSessionCommand,
    SubmitAudioTurnCommand,
    SubmitTextTurnCommand,
)
from app.application.facades.sustentacion_facade import SustentacionFacade
from app.core.container import Container
from app.domain.builders.acta_report_data import ActaExportFormat
from app.domain.entities.defense_enums import JuryProfile
from app.presentation.api.dependencies import get_container, get_defense_facade
from app.presentation.api.v1.schemas.defense_http_schemas import (
    CreateDefenseSessionRequestSchema,
    DefenseSessionResponseSchema,
    SubmitTextTurnRequestSchema,
    TtsSynthesizeRequestSchema,
    TurnSubmissionResponseSchema,
)
from app.presentation.api.v1.schemas.fdc_http_schemas import ErrorResponseSchema

router = APIRouter(prefix="/defense", tags=["Módulo 2 · Sustentación AURA"])

_DEFENSE_ERRORS = {
    404: {"model": ErrorResponseSchema, "description": "Sesión o documento FDC no encontrado."},
    409: {"model": ErrorResponseSchema, "description": "Transición inválida de estado en sustentación."},
    413: {"model": ErrorResponseSchema, "description": "Audio excede tamaño máximo permitido."},
    415: {"model": ErrorResponseSchema, "description": "Formato de audio no soportado."},
    422: {"model": ErrorResponseSchema, "description": "Audio ininteligible, respuesta muy corta o perfil inválido."},
    502: {"model": ErrorResponseSchema, "description": "Error de comunicación con Gemini."},
    503: {"model": ErrorResponseSchema, "description": "GEMINI_API_KEY no configurada."},
}


@router.post(
    "/sessions",
    response_model=DefenseSessionResponseSchema,
    status_code=201,
    responses=_DEFENSE_ERRORS,
    summary="Crear sesión de sustentación desde un documento FDC analizado",
)
async def create_defense_session(
    payload: CreateDefenseSessionRequestSchema,
    facade: SustentacionFacade = Depends(get_defense_facade),
) -> DefenseSessionResponseSchema:
    cmd = CreateDefenseSessionCommand(
        fdc_document_id=payload.fdc_document_id,
        jury_profile=JuryProfile(payload.jury_profile),
    )
    view = await run_in_threadpool(facade.create_session, cmd)
    return DefenseSessionResponseSchema.from_view(view)


@router.get(
    "/sessions/{session_id}",
    response_model=DefenseSessionResponseSchema,
    responses=_DEFENSE_ERRORS,
    summary="Consultar estado, turnos y pregunta activa de la sustentación",
)
def get_defense_session(
    session_id: UUID,
    facade: SustentacionFacade = Depends(get_defense_facade),
) -> DefenseSessionResponseSchema:
    view = facade.get_session(session_id)
    return DefenseSessionResponseSchema.from_view(view)


@router.post(
    "/sessions/{session_id}/tts",
    responses=_DEFENSE_ERRORS,
    summary="Sintetizar a audio (WAV/MP3) la pregunta actual de AURA",
)
async def synthesize_aura_speech(
    session_id: UUID,
    payload: TtsSynthesizeRequestSchema | None = Body(default=None),
    facade: SustentacionFacade = Depends(get_defense_facade),
) -> Response:
    audio = await run_in_threadpool(
        facade.synthesize_speech,
        session_id,
        payload.text if payload else None,
    )
    return Response(
        content=audio.audio_bytes,
        media_type=audio.mime_type,
        headers={"X-Tutoia-Tts-Model": audio.model_used},
    )


@router.post(
    "/sessions/{session_id}/turns/audio",
    response_model=TurnSubmissionResponseSchema,
    responses=_DEFENSE_ERRORS,
    summary="Enviar respuesta grabada en audio para transcripción y evaluación",
)
async def submit_audio_turn(
    session_id: UUID,
    audio: UploadFile = File(...),
    container: Container = Depends(get_container),
    facade: SustentacionFacade = Depends(get_defense_facade),
) -> TurnSubmissionResponseSchema:
    max_bytes = container.settings.defense_max_audio_bytes
    audio_bytes = await audio.read(max_bytes + 1)
    cmd = SubmitAudioTurnCommand(
        session_id=session_id,
        audio_bytes=audio_bytes,
        mime_type=audio.content_type or "",
        filename=audio.filename or "respuesta.webm",
    )
    result = await run_in_threadpool(facade.submit_audio_turn, cmd)
    return TurnSubmissionResponseSchema.from_result(result)


@router.post(
    "/sessions/{session_id}/turns/text",
    response_model=TurnSubmissionResponseSchema,
    responses=_DEFENSE_ERRORS,
    summary="Enviar respuesta escrita (respaldo sin micrófono o edición manual)",
)
async def submit_text_turn(
    session_id: UUID,
    payload: SubmitTextTurnRequestSchema,
    facade: SustentacionFacade = Depends(get_defense_facade),
) -> TurnSubmissionResponseSchema:
    cmd = SubmitTextTurnCommand(
        session_id=session_id,
        transcript_text=payload.text,
    )
    result = await run_in_threadpool(facade.submit_text_turn, cmd)
    return TurnSubmissionResponseSchema.from_result(result)


@router.get(
    "/sessions/{session_id}/report",
    responses={
        200: {"description": "Acta oficial generada en PDF o Word (.docx)."},
        404: _DEFENSE_ERRORS[404],
        409: _DEFENSE_ERRORS[409],
    },
    summary="Exportar el Acta Oficial de Sustentación en PDF o DOCX",
)
async def export_defense_acta(
    session_id: UUID,
    format: Literal["pdf", "docx"] = Query(default="pdf", description="Formato de exportación: pdf o docx."),
    facade: SustentacionFacade = Depends(get_defense_facade),
) -> Response:
    exported = await run_in_threadpool(facade.export_acta, session_id, ActaExportFormat(format))
    return Response(
        content=exported.content,
        media_type=exported.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{exported.filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
