"""Caso de uso: ensamblar y exportar el Acta Oficial de Sustentación (PDF/DOCX)."""
from datetime import datetime, timezone
from uuid import UUID

from app.application.dto.defense_dtos import ActaExportResult
from app.domain.builders.acta_report_data import (
    ActaCriterionRow,
    ActaExportFormat,
    ActaReportData,
    ActaTurnEntry,
)
from app.domain.builders.defense_acta_builder import DefenseActaDirector
from app.domain.entities.defense_enums import DefenseStateStatus, JuryProfile
from app.domain.entities.fdc_document import FdcType, Modality
from app.domain.exceptions.defense_exceptions import (
    DefenseSessionNotCompletedError,
    DefenseSessionNotFoundError,
)
from app.domain.exceptions.fdc_exceptions import FdcDocumentNotFoundError
from app.domain.ports.acta_builder_port import ActaBuilderFactoryPort
from app.domain.ports.defense_repository_port import DefenseSessionRepositoryPort
from app.domain.ports.repositories import FdcDocumentRepositoryPort, ProjectRepositoryPort
from app.domain.ports.rubric_provider_port import RubricProviderPort

_MIME_BY_FORMAT: dict[ActaExportFormat, str] = {
    ActaExportFormat.PDF: "application/pdf",
    ActaExportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_FDC_LABELS: dict[FdcType, str] = {
    FdcType.FDC_124: "F-DC-124 · Propuesta de Trabajo de Grado",
    FdcType.FDC_125: "F-DC-125 · Informe Final de Trabajo de Grado",
}
_MODALITY_LABELS: dict[Modality, str] = {
    Modality.DESARROLLO_TECNOLOGICO: "Desarrollo Tecnológico",
    Modality.INVESTIGACION: "Proyecto de Investigación",
    Modality.MONOGRAFIA: "Monografía",
    Modality.EMPRENDIMIENTO: "Emprendimiento",
}
_JURY_LABELS: dict[JuryProfile, str] = {
    JuryProfile.ESTANDAR_UTS: "Jurado Estándar UTS",
    JuryProfile.TECNICO_RIGUROSO: "Jurado Técnico Riguroso",
}


class ExportDefenseActaUseCase:
    """Orquesta recuperación documental y construcción vía DefenseActaDirector."""

    def __init__(
        self,
        project_repo: ProjectRepositoryPort,
        document_repo: FdcDocumentRepositoryPort,
        defense_repo: DefenseSessionRepositoryPort,
        rubric_provider: RubricProviderPort,
        builder_factory: ActaBuilderFactoryPort,
    ) -> None:
        self._project_repo = project_repo
        self._document_repo = document_repo
        self._defense_repo = defense_repo
        self._rubric_provider = rubric_provider
        self._builder_factory = builder_factory

    def execute(self, session_id: UUID, export_format: ActaExportFormat) -> ActaExportResult:
        session = self._defense_repo.get_session(session_id)
        if session is None:
            raise DefenseSessionNotFoundError(
                message=f"No existe la sesión de sustentación '{session_id}'.",
                context={"session_id": str(session_id)},
            )
        if session.state != DefenseStateStatus.COMPLETED or session.final_summary is None:
            raise DefenseSessionNotCompletedError(
                message="El acta oficial solo puede exportarse cuando la sustentación ha finalizado (COMPLETED).",
                context={"session_id": str(session_id), "state": session.state.value},
            )

        document = self._document_repo.get(session.fdc_document_id)
        if document is None:
            raise FdcDocumentNotFoundError(
                "Documento FDC asociado no encontrado.",
                context={"document_id": str(session.fdc_document_id)},
            )
        project = self._project_repo.get(document.project_id)
        if project is None:
            raise FdcDocumentNotFoundError(
                "Proyecto asociado no encontrado.",
                context={"project_id": str(document.project_id)},
            )

        turns = self._defense_repo.list_turns(session.id)
        rubric = self._rubric_provider.get_rubric()
        summary = session.final_summary
        now = datetime.now(timezone.utc)

        criteria_rows = tuple(
            ActaCriterionRow(
                code=crit.code,
                label=crit.label,
                weight_percent=round(crit.weight * 100),
                average_score=round(summary.criteria_averages.get(crit.code, 0.0), 2),
                weighted_contribution=round(
                    summary.criteria_averages.get(crit.code, 0.0) * crit.weight, 2
                ),
            )
            for crit in rubric.criteria
        )
        turn_entries = tuple(
            ActaTurnEntry(
                turn_number=t.turn_number,
                question_index=t.question_index,
                is_follow_up=t.is_follow_up,
                thematic_axis=t.thematic_axis,
                aura_question=t.aura_question_text,
                student_transcript=t.student_transcript,
                input_mode=t.input_mode.value,
                weighted_score=t.rubric_scores.weighted_score,
                turn_feedback=t.turn_feedback,
            )
            for t in turns
        )
        authors = tuple(
            f"{a.full_name} ({a.student_code})" if a.student_code else a.full_name
            for a in project.authors
            if a.full_name.strip()
        )

        report_data = ActaReportData(
            session_id=str(session.id),
            generated_at=now.strftime("%Y-%m-%d %H:%M UTC"),
            completed_at=(session.completed_at or now).strftime("%Y-%m-%d %H:%M UTC"),
            fdc_type_label=_FDC_LABELS.get(document.fdc_type, document.fdc_type.value),
            project_title=project.title,
            academic_program=project.academic_program,
            modality_label=_MODALITY_LABELS.get(project.modality, project.modality.value),
            director_name=project.director_name or "No especificado",
            authors=authors,
            jury_profile_label=_JURY_LABELS.get(session.jury_profile, session.jury_profile.value),
            rubric_name=f"{rubric.name} ({rubric.period})",
            overall_score=session.overall_score or 0.0,
            verdict=summary.verdict.value,
            closing_message=summary.closing_message,
            criteria_rows=criteria_rows,
            strengths=tuple(summary.strengths),
            improvements=tuple(summary.improvements),
            turns=turn_entries,
            human_in_the_loop_notice=summary.human_in_the_loop_notice,
        )

        builder = self._builder_factory.create(export_format)
        content = DefenseActaDirector(builder).construct(report_data)
        short_id = str(session.id).split("-")[0]
        return ActaExportResult(
            content=content,
            mime_type=_MIME_BY_FORMAT[export_format],
            filename=f"Acta_Sustentacion_UTS_{short_id}.{export_format.value}",
        )
