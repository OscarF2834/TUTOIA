"""Repositorios SQLAlchemy 2.0 y Unit of Work para el módulo FDC."""
from dataclasses import asdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.fdc_analysis import (
    AcademicSynthesis,
    CoherenceFinding,
    DefenseGap,
    ExecutionMetrics,
    FdcAnalysis,
)
from app.domain.entities.fdc_document import FdcDocument, FdcType, IngestionStatus, Modality
from app.domain.entities.project import Author, Project, ProjectStatus
from app.infrastructure.db.models.fdc_analysis_model import FdcAnalysisModel
from app.infrastructure.db.models.fdc_document_model import FdcDocumentModel
from app.infrastructure.db.models.project_model import ProjectModel


class SqlAlchemyProjectRepository:
    """Repositorio SQLAlchemy para Project."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, project: Project) -> None:
        model = ProjectModel(
            id=project.id,
            title=project.title,
            academic_program=project.academic_program,
            modality=project.modality.value,
            authors=[asdict(a) for a in project.authors],
            director_name=project.director_name,
            status=project.status.value,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        self._session.add(model)

    def get(self, project_id: UUID) -> Project | None:
        model = self._session.get(ProjectModel, project_id)
        if model is None:
            return None
        return Project(
            id=model.id,
            title=model.title,
            academic_program=model.academic_program,
            modality=Modality(model.modality),
            authors=[Author(**item) for item in model.authors],
            director_name=model.director_name,
            status=ProjectStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SqlAlchemyFdcDocumentRepository:
    """Repositorio SQLAlchemy para FdcDocument."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, document: FdcDocument) -> None:
        model = FdcDocumentModel(
            id=document.id,
            project_id=document.project_id,
            fdc_type=document.fdc_type.value,
            original_filename=document.original_filename,
            mime_type=document.mime_type,
            file_size_bytes=document.file_size_bytes,
            sha256_hash=document.sha256_hash,
            storage_path=document.storage_path,
            gemini_file_name=document.gemini_file_name,
            gemini_file_uri=document.gemini_file_uri,
            gemini_file_expires_at=document.gemini_file_expires_at,
            ingestion_status=document.ingestion_status.value,
            created_at=document.created_at,
        )
        self._session.add(model)

    def get(self, document_id: UUID) -> FdcDocument | None:
        model = self._session.get(FdcDocumentModel, document_id)
        if model is None:
            return None
        return FdcDocument(
            id=model.id,
            project_id=model.project_id,
            fdc_type=FdcType(model.fdc_type),
            original_filename=model.original_filename,
            mime_type=model.mime_type,
            file_size_bytes=model.file_size_bytes,
            sha256_hash=model.sha256_hash,
            storage_path=model.storage_path,
            gemini_file_name=model.gemini_file_name,
            gemini_file_uri=model.gemini_file_uri,
            gemini_file_expires_at=model.gemini_file_expires_at,
            ingestion_status=IngestionStatus(model.ingestion_status),
            created_at=model.created_at,
        )


class SqlAlchemyFdcAnalysisRepository:
    """Repositorio SQLAlchemy para FdcAnalysis."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, analysis: FdcAnalysis) -> None:
        coherence_payload = {
            "overall_level": analysis.overall_coherence_level,
            "findings": [asdict(f) for f in analysis.coherence_findings],
        }
        model = FdcAnalysisModel(
            id=analysis.id,
            fdc_document_id=analysis.fdc_document_id,
            strategy_name=analysis.strategy_name,
            model_name=analysis.model_name,
            schema_version=analysis.schema_version,
            academic_synthesis=asdict(analysis.academic_synthesis),
            coherence_findings=coherence_payload,
            detected_gaps=[asdict(g) for g in analysis.detected_gaps],
            execution_metrics=asdict(analysis.execution_metrics),
            created_at=analysis.created_at,
        )
        self._session.add(model)

    def get_by_document_id(self, document_id: UUID) -> FdcAnalysis | None:
        model = (
            self._session.query(FdcAnalysisModel)
            .filter(FdcAnalysisModel.fdc_document_id == document_id)
            .one_or_none()
        )
        if model is None:
            return None
        coherence_payload = model.coherence_findings
        return FdcAnalysis(
            id=model.id,
            fdc_document_id=model.fdc_document_id,
            strategy_name=model.strategy_name,
            model_name=model.model_name,
            schema_version=model.schema_version,
            academic_synthesis=AcademicSynthesis(**model.academic_synthesis),
            overall_coherence_level=coherence_payload["overall_level"],
            coherence_findings=[CoherenceFinding(**item) for item in coherence_payload["findings"]],
            detected_gaps=[DefenseGap(**item) for item in model.detected_gaps],
            execution_metrics=ExecutionMetrics(**model.execution_metrics),
            created_at=model.created_at,
        )


class SqlAlchemyUnitOfWork:
    """Control transaccional sobre la sesión SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
