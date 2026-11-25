"""Contenedor de composición e inyección de dependencias del Módulo 1."""
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.facades.fdc_ingestion_facade import FdcIngestionFacade
from app.application.observers.event_bus import AuditLogObserver, InMemoryEventBus
from app.application.pipelines.fdc_ingestion.base_handler import IngestionHandler
from app.application.pipelines.fdc_ingestion.fdc_structure_handler import FdcStructureHandler
from app.application.pipelines.fdc_ingestion.gemini_upload_handler import GeminiUploadHandler
from app.application.pipelines.fdc_ingestion.mime_extension_handler import MimeExtensionHandler
from app.application.pipelines.fdc_ingestion.size_integrity_handler import SizeIntegrityHandler
from app.application.pipelines.fdc_ingestion.text_readability_handler import TextReadabilityHandler
from app.application.use_cases.get_fdc_analysis import GetFdcAnalysisUseCase
from app.application.use_cases.ingest_and_analyze_fdc import IngestAndAnalyzeFdcUseCase
from app.core.settings import Settings
from app.domain.events.fdc_events import FdcDocumentAnalyzedEvent, FdcIngestionFailedEvent
from app.domain.ports.ai_fdc_analyzer_port import AiFdcAnalyzerPort
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy
from app.infrastructure.adapters.document_reader_adapter import DocumentReaderAdapter
from app.infrastructure.adapters.gemini_genai_adapter import GeminiGenAiAdapter
from app.infrastructure.db import models  # noqa: F401
from app.infrastructure.db.base import Base
from app.infrastructure.db.repositories.sqlalchemy_fdc_repositories import (
    SqlAlchemyFdcAnalysisRepository,
    SqlAlchemyFdcDocumentRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemyUnitOfWork,
)
from app.infrastructure.db.session import build_engine
from app.infrastructure.storage.local_file_storage import LocalFileStorage


class Container:
    """Ensambla adaptadores, repositorios, pipeline y fachadas."""

    def __init__(
        self,
        settings: Settings,
        analyzer: AiFdcAnalyzerPort | None = None,
        engine: Engine | None = None,
    ) -> None:
        self.settings = settings
        self.engine = engine or build_engine(settings.DATABASE_URL)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )
        self.storage = LocalFileStorage(settings.FDC_STORAGE_DIR)
        self.reader = DocumentReaderAdapter()
        self.analyzer: AiFdcAnalyzerPort = analyzer or GeminiGenAiAdapter(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_ANALYSIS_MODEL,
            timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
        )
        self.event_bus = InMemoryEventBus()
        audit_observer = AuditLogObserver()
        self.event_bus.subscribe(FdcDocumentAnalyzedEvent, audit_observer.on_analyzed)
        self.event_bus.subscribe(FdcIngestionFailedEvent, audit_observer.on_failed)

    def init_db(self) -> None:
        """Crea las tablas registradas si aún no existen."""
        Base.metadata.create_all(bind=self.engine)

    def build_pipeline(self, _strategy: FdcAnalysisStrategy) -> IngestionHandler:
        """Construye la cadena Chain of Responsibility de ingesta FDC."""
        head = SizeIntegrityHandler(max_bytes=self.settings.fdc_max_upload_bytes)
        (
            head.set_next(MimeExtensionHandler())
            .set_next(
                TextReadabilityHandler(
                    reader=self.reader,
                    min_chars=self.settings.FDC_MIN_TEXT_CHARS,
                )
            )
            .set_next(FdcStructureHandler())
            .set_next(GeminiUploadHandler(analyzer=self.analyzer))
        )
        return head

    def fdc_facade(self, session: Session) -> FdcIngestionFacade:
        """Construye FdcIngestionFacade con repositorios ligados a la sesión."""
        project_repo = SqlAlchemyProjectRepository(session)
        document_repo = SqlAlchemyFdcDocumentRepository(session)
        analysis_repo = SqlAlchemyFdcAnalysisRepository(session)
        uow = SqlAlchemyUnitOfWork(session)

        ingest_uc = IngestAndAnalyzeFdcUseCase(
            pipeline_builder=self.build_pipeline,
            storage=self.storage,
            analyzer=self.analyzer,
            project_repo=project_repo,
            document_repo=document_repo,
            analysis_repo=analysis_repo,
            uow=uow,
            event_bus=self.event_bus,
        )
        get_uc = GetFdcAnalysisUseCase(
            project_repo=project_repo,
            document_repo=document_repo,
            analysis_repo=analysis_repo,
        )
        return FdcIngestionFacade(ingest_use_case=ingest_uc, get_use_case=get_uc)
