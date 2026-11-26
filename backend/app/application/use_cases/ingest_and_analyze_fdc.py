"""Caso de uso: ingesta validada y análisis estructurado de documentos FDC."""
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.application.dto.fdc_ingestion_dto import (
    FdcDocumentView,
    FdcIngestionContext,
    FdcUploadCommand,
)
from app.application.observers.event_bus import InMemoryEventBus
from app.application.pipelines.fdc_ingestion.base_handler import IngestionHandler
from app.domain.entities.fdc_analysis import FdcAnalysis, FdcExtraction
from app.domain.entities.fdc_document import FdcDocument, IngestionStatus
from app.domain.entities.project import Project, ProjectStatus
from app.domain.events.fdc_events import FdcDocumentAnalyzedEvent, FdcIngestionFailedEvent
from app.domain.exceptions.fdc_exceptions import FdcDomainError
from app.domain.factories.fdc_strategy_factory import FdcStrategyFactory
from app.domain.ports.ai_fdc_analyzer_port import AiFdcAnalyzerPort
from app.domain.ports.file_storage_port import FileStoragePort
from app.domain.ports.repositories import (
    FdcAnalysisRepositoryPort,
    FdcDocumentRepositoryPort,
    ProjectRepositoryPort,
    UnitOfWorkPort,
)
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy


class IngestAndAnalyzeFdcUseCase:
    """Orquesta pipeline Chain of Responsibility, Strategy, Adapter y persistencia."""

    def __init__(
        self,
        pipeline_builder: Callable[[FdcAnalysisStrategy], IngestionHandler],
        storage: FileStoragePort,
        analyzer: AiFdcAnalyzerPort,
        project_repo: ProjectRepositoryPort,
        document_repo: FdcDocumentRepositoryPort,
        analysis_repo: FdcAnalysisRepositoryPort,
        uow: UnitOfWorkPort,
        event_bus: InMemoryEventBus,
    ) -> None:
        self._pipeline_builder = pipeline_builder
        self._storage = storage
        self._analyzer = analyzer
        self._project_repo = project_repo
        self._document_repo = document_repo
        self._analysis_repo = analysis_repo
        self._uow = uow
        self._event_bus = event_bus

    def execute(self, cmd: FdcUploadCommand) -> FdcDocumentView:
        """Ejecuta validación, almacenamiento, análisis IA y persistencia transaccional."""
        try:
            strategy = FdcStrategyFactory.create(cmd.fdc_type, modality=cmd.modality)
            ctx = FdcIngestionContext(filename=cmd.filename, content=cmd.content, strategy=strategy)
            self._pipeline_builder(strategy).handle(ctx)

            storage_path = self._storage.save(ctx.content, ctx.extension)
            extraction, metrics = self._analyzer.analyze(ctx.remote_file, strategy)  # type: ignore[arg-type]

            now = datetime.now(timezone.utc)
            project = self._build_project(cmd, extraction, now)
            document = self._build_document(cmd, ctx, project, storage_path, now)
            analysis = self._build_analysis(document, strategy, extraction, metrics, now)

            self._project_repo.add(project)
            self._document_repo.add(document)
            self._analysis_repo.add(analysis)
            self._uow.commit()

            self._event_bus.publish(
                FdcDocumentAnalyzedEvent(
                    document_id=document.id,
                    project_id=project.id,
                    fdc_type=document.fdc_type.value,
                    strategy_name=strategy.name,
                    latency_ms=metrics.latency_ms,
                    occurred_at=now,
                )
            )
            return FdcDocumentView(project=project, document=document, analysis=analysis)
        except FdcDomainError as exc:
            self._uow.rollback()
            self._event_bus.publish(
                FdcIngestionFailedEvent(
                    filename=cmd.filename,
                    error_code=exc.code,
                    occurred_at=datetime.now(timezone.utc),
                )
            )
            raise

    @staticmethod
    def _build_project(cmd: FdcUploadCommand, extraction: FdcExtraction, now: datetime) -> Project:
        program = (cmd.academic_program or "").strip() or extraction.detected_academic_program
        modality = cmd.modality or extraction.detected_modality
        return Project(
            id=uuid4(),
            title=extraction.title,
            academic_program=program,
            modality=modality,
            authors=extraction.authors,
            director_name=extraction.director_name,
            status=ProjectStatus.ANALYZED,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _build_document(
        cmd: FdcUploadCommand,
        ctx: FdcIngestionContext,
        project: Project,
        storage_path: str,
        now: datetime,
    ) -> FdcDocument:
        safe_name = Path(cmd.filename).name
        remote = ctx.remote_file
        return FdcDocument(
            id=uuid4(),
            project_id=project.id,
            fdc_type=cmd.fdc_type,
            original_filename=safe_name,
            mime_type=ctx.mime_type,
            file_size_bytes=ctx.size_bytes,
            sha256_hash=ctx.sha256,
            storage_path=storage_path,
            gemini_file_name=remote.name if remote else None,
            gemini_file_uri=remote.uri if remote else None,
            gemini_file_expires_at=remote.expires_at if remote else None,
            ingestion_status=IngestionStatus.ANALYZED,
            created_at=now,
        )

    def _build_analysis(
        self,
        document: FdcDocument,
        strategy: FdcAnalysisStrategy,
        extraction: FdcExtraction,
        metrics,
        now: datetime,
    ) -> FdcAnalysis:
        return FdcAnalysis(
            id=uuid4(),
            fdc_document_id=document.id,
            strategy_name=strategy.name,
            model_name=metrics.model_used or self._analyzer.model_name,
            schema_version="1.0",
            academic_synthesis=extraction.synthesis,
            overall_coherence_level=extraction.overall_coherence_level,
            coherence_findings=extraction.coherence_findings,
            detected_gaps=extraction.detected_gaps,
            execution_metrics=metrics,
            created_at=now,
        )
