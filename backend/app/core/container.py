"""Contenedor de composición e inyección de dependencias (Módulos 1 y 2)."""
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.facades.fdc_ingestion_facade import FdcIngestionFacade
from app.application.facades.sustentacion_facade import SustentacionFacade
from app.application.observers.event_bus import AuditLogObserver, InMemoryEventBus
from app.application.pipelines.fdc_ingestion.base_handler import IngestionHandler
from app.application.pipelines.fdc_ingestion.fdc_structure_handler import FdcStructureHandler
from app.application.pipelines.fdc_ingestion.gemini_upload_handler import GeminiUploadHandler
from app.application.pipelines.fdc_ingestion.mime_extension_handler import MimeExtensionHandler
from app.application.pipelines.fdc_ingestion.size_integrity_handler import SizeIntegrityHandler
from app.application.pipelines.fdc_ingestion.text_readability_handler import TextReadabilityHandler
from app.application.use_cases.create_defense_session import CreateDefenseSessionUseCase
from app.application.use_cases.get_defense_session import GetDefenseSessionUseCase
from app.application.use_cases.get_fdc_analysis import GetFdcAnalysisUseCase
from app.application.use_cases.ingest_and_analyze_fdc import IngestAndAnalyzeFdcUseCase
from app.application.use_cases.submit_defense_turn import SubmitDefenseTurnUseCase
from app.application.use_cases.synthesize_aura_speech import SynthesizeAuraSpeechUseCase
from app.core.settings import Settings
from app.domain.events.defense_events import (
    DefenseSessionCompletedEvent,
    DefenseSessionCreatedEvent,
    DefenseTurnEvaluatedEvent,
)
from app.domain.events.fdc_events import FdcDocumentAnalyzedEvent, FdcIngestionFailedEvent
from app.domain.ports.ai_fdc_analyzer_port import AiFdcAnalyzerPort
from app.domain.ports.defense_ai_ports import (
    DefenseAiDialogPort,
    SpeechSttPort,
    SpeechTtsPort,
)
from app.domain.ports.rubric_provider_port import RubricProviderPort
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy
from app.infrastructure.adapters.document_reader_adapter import DocumentReaderAdapter
from app.infrastructure.adapters.gemini_defense_dialog_adapter import GeminiDefenseDialogAdapter
from app.infrastructure.adapters.gemini_genai_adapter import GeminiGenAiAdapter
from app.infrastructure.adapters.gemini_transcribe_adapter import GeminiTranscribeAdapter
from app.infrastructure.adapters.gemini_tts_adapter import GeminiTtsAdapter
from app.infrastructure.adapters.json_rubric_provider_adapter import JsonRubricProviderAdapter
from app.infrastructure.adapters.resilient_ai_analyzer import ResilientAiAnalyzer
from app.infrastructure.db import models  # noqa: F401
from app.infrastructure.db.base import Base
from app.infrastructure.db.repositories.sqlalchemy_defense_repository import (
    SqlAlchemyDefenseRepository,
)
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
        dialog_adapter: DefenseAiDialogPort | None = None,
        tts_adapter: SpeechTtsPort | None = None,
        stt_adapter: SpeechSttPort | None = None,
        rubric_provider: RubricProviderPort | None = None,
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
        self.analyzer = self._build_analyzer(settings, analyzer)
        self.rubric_provider: RubricProviderPort = rubric_provider or JsonRubricProviderAdapter(
            settings.RUBRICS_DIR / "rubrica_uts.json"
        )
        self.dialog_adapter: DefenseAiDialogPort = dialog_adapter or GeminiDefenseDialogAdapter(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_DIALOG_MODEL,
            fallback_models=settings.gemini_dialog_fallback_models,
            timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
            max_retries=settings.GEMINI_MAX_RETRIES,
            base_delay_seconds=settings.GEMINI_RETRY_BASE_DELAY_SECONDS,
        )
        self.tts_adapter: SpeechTtsPort = tts_adapter or GeminiTtsAdapter(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_TTS_MODEL,
            fallback_models=settings.gemini_tts_fallback_models,
            voice=settings.GEMINI_TTS_VOICE,
            timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
            max_retries=settings.GEMINI_MAX_RETRIES,
            base_delay_seconds=settings.GEMINI_RETRY_BASE_DELAY_SECONDS,
        )
        self.stt_adapter: SpeechSttPort = stt_adapter or GeminiTranscribeAdapter(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_TRANSCRIBE_MODEL,
            max_audio_bytes=settings.defense_max_audio_bytes,
            timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
            max_retries=settings.GEMINI_MAX_RETRIES,
            base_delay_seconds=settings.GEMINI_RETRY_BASE_DELAY_SECONDS,
        )
        self.event_bus = self._build_event_bus()

    @staticmethod
    def _build_analyzer(
        settings: Settings,
        analyzer: AiFdcAnalyzerPort | None,
    ) -> AiFdcAnalyzerPort:
        if analyzer is not None:
            return analyzer
        raw_gemini = GeminiGenAiAdapter(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_ANALYSIS_MODEL,
            timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
        )
        return ResilientAiAnalyzer(
            inner=raw_gemini,
            fallback_models=settings.gemini_fallback_models,
            max_retries=settings.GEMINI_MAX_RETRIES,
            base_delay_seconds=settings.GEMINI_RETRY_BASE_DELAY_SECONDS,
        )

    @staticmethod
    def _build_event_bus() -> InMemoryEventBus:
        bus = InMemoryEventBus()
        audit = AuditLogObserver()
        bus.subscribe(FdcDocumentAnalyzedEvent, audit.on_analyzed)
        bus.subscribe(FdcIngestionFailedEvent, audit.on_failed)
        bus.subscribe(DefenseSessionCreatedEvent, audit.on_defense_created)
        bus.subscribe(DefenseTurnEvaluatedEvent, audit.on_defense_turn)
        bus.subscribe(DefenseSessionCompletedEvent, audit.on_defense_completed)
        return bus

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

    def defense_facade(self, session: Session) -> SustentacionFacade:
        """Construye SustentacionFacade del Módulo 2 con repositorios ligados a la sesión."""
        project_repo = SqlAlchemyProjectRepository(session)
        document_repo = SqlAlchemyFdcDocumentRepository(session)
        analysis_repo = SqlAlchemyFdcAnalysisRepository(session)
        defense_repo = SqlAlchemyDefenseRepository(session)
        uow = SqlAlchemyUnitOfWork(session)

        return SustentacionFacade(
            create_uc=CreateDefenseSessionUseCase(
                project_repo=project_repo,
                document_repo=document_repo,
                analysis_repo=analysis_repo,
                defense_repo=defense_repo,
                dialog_port=self.dialog_adapter,
                uow=uow,
                event_bus=self.event_bus,
            ),
            get_uc=GetDefenseSessionUseCase(defense_repo=defense_repo),
            tts_uc=SynthesizeAuraSpeechUseCase(
                defense_repo=defense_repo,
                tts_port=self.tts_adapter,
                uow=uow,
            ),
            submit_turn_uc=SubmitDefenseTurnUseCase(
                project_repo=project_repo,
                document_repo=document_repo,
                analysis_repo=analysis_repo,
                defense_repo=defense_repo,
                rubric_provider=self.rubric_provider,
                dialog_port=self.dialog_adapter,
                stt_port=self.stt_adapter,
                uow=uow,
                event_bus=self.event_bus,
                min_words=self.settings.DEFENSE_MIN_WORDS,
            ),
        )
