"""Fixtures y helpers compartidos para pruebas unitarias e integración."""
from datetime import datetime, timedelta, timezone
import io
from pathlib import Path

import docx
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.core.container import Container
from app.core.settings import Settings
from app.domain.entities.fdc_analysis import (
    AcademicSynthesis,
    CoherenceFinding,
    DefenseGap,
    ExecutionMetrics,
    FdcExtraction,
)
from app.domain.entities.fdc_document import Modality
from app.domain.entities.project import Author
from app.domain.events.fdc_events import FdcDocumentAnalyzedEvent, FdcIngestionFailedEvent
from app.domain.ports.ai_fdc_analyzer_port import RemoteFileRef
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy
from app.presentation.app_factory import register_fdc_module

FDC_124_LINES = [
    "FORMATO F-DC-124 PROPUESTA DE TRABAJO DE GRADO UTS",
    "Titulo: Plataforma inteligente de apoyo a sustentaciones academicas.",
    "Planteamiento del problema:",
    "En las Unidades Tecnologicas de Santander se evidencia una alta carga operativa para",
    "los comites evaluadores al revisar propuestas y preparar preguntas contextualizadas",
    "de sustentacion de grado, lo cual genera heterogeneidad en los criterios aplicados.",
    "Objetivo general:",
    "Disenar e implementar un modulo de analisis documental automatizado basado en PLN.",
    "Objetivos especificos:",
    "1. Estructurar la ingesta y validacion de documentos academicos en formato FDC.",
    "2. Evaluar coherencia entre problema, objetivos y diseno metodologico propuesto.",
    "Metodologia:",
    "El proyecto sigue un enfoque de desarrollo tecnologico iterativo bajo arquitectura limpia,",
    "patrones de diseno de Refactoring Guru, persistencia relacional en SQLAlchemy y pruebas",
    "automatizadas con casos reales anonimizados de la Facultad de Ciencias Naturales e Ingenierias.",
]

FDC_125_LINES = FDC_124_LINES + [
    "Resultados:",
    "Se implemento el modulo completo logrando un 94 por ciento de precision en extraccion",
    "estructurada de objetivos y vacios metodologicos sobre una muestra de 30 documentos.",
    "Conclusiones:",
    "La integracion desacoplada con modelos multimodales reduce los tiempos de revision previa",
    "y estandariza la preparacion de preguntas de sustentacion bajo supervision docente.",
]


def _escape_pdf_text(text: str) -> str:
    ascii_text = text.encode("ascii", "replace").decode("ascii")
    return ascii_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(lines: list[str]) -> bytes:
    """Construye un PDF mínimo válido en memoria con xref exacto."""
    if lines:
        ops = ["BT", "/F1 11 Tf", "14 TL", "50 780 Td"]
        for idx, line in enumerate(lines):
            escaped = _escape_pdf_text(line)
            ops.append(f"({escaped}) Tj" if idx == 0 else f"T* ({escaped}) Tj")
        ops.append("ET")
        stream_bytes = "\n".join(ops).encode("ascii")
    else:
        stream_bytes = b""

    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        ),
        (
            b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
            b"/Encoding /WinAnsiEncoding >>\nendobj\n"
        ),
        (
            f"5 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
            + stream_bytes
            + b"\nendstream\nendobj\n"
        ),
    ]

    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(buffer.tell())
        buffer.write(obj)

    xref_pos = buffer.tell()
    buffer.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    buffer.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "ascii"
        )
    )
    return buffer.getvalue()


def build_docx(paragraphs: list[str]) -> bytes:
    """Construye un archivo DOCX válido en memoria."""
    document = docx.Document()
    for text in paragraphs:
        document.add_paragraph(text)
    out = io.BytesIO()
    document.save(out)
    return out.getvalue()


class FakeAiAnalyzer:
    """Mock determinista de AiFdcAnalyzerPort para pruebas sin red ni cuota."""

    def __init__(self) -> None:
        self.model_name = "fake-model"
        self.upload_calls: list[dict] = []
        self.analyze_calls: list[dict] = []

    def upload_document(
        self,
        content: bytes,
        mime_type: str,
        display_name: str,
        extracted_text: str,
    ) -> RemoteFileRef:
        self.upload_calls.append(
            {
                "size": len(content),
                "mime_type": mime_type,
                "display_name": display_name,
                "text_len": len(extracted_text),
            }
        )
        return RemoteFileRef(
            name="files/fake123",
            uri="https://fake/files/fake123",
            mime_type=mime_type,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
        )

    def analyze(
        self,
        file_ref: RemoteFileRef,
        strategy: FdcAnalysisStrategy,
    ) -> tuple[FdcExtraction, ExecutionMetrics]:
        self.analyze_calls.append({"uri": file_ref.uri, "strategy": strategy.name})
        extraction = FdcExtraction(
            title="Plataforma inteligente de apoyo a sustentaciones académicas",
            authors=[Author(full_name="Ana María Sofán Ruiz", student_code="1098765432")],
            director_name="Jaidiver Lombo Guzmán",
            detected_academic_program="Ingeniería de Sistemas",
            detected_modality=Modality.DESARROLLO_TECNOLOGICO,
            synthesis=AcademicSynthesis(
                central_problem="Falta de estandarización al analizar FDC y preparar preguntas de grado.",
                research_question="¿Cómo automatizar el diagnóstico documental previo a la sustentación?",
                justification_summary="Reduce tiempos operativos de revisión en la FCNI.",
                general_objective="Implementar un módulo de análisis documental automatizado.",
                specific_objectives=[
                    "Validar documentos FDC en cadena.",
                    "Detectar vacíos argumentales para la sustentación.",
                ],
                research_type_and_approach="Desarrollo tecnológico iterativo",
                phases_or_stages=["Ingesta", "Análisis estructurado", "Validación"],
                technologies_and_instruments=["FastAPI", "SQLAlchemy", "Google Gemini"],
                validation_scope="30 proyectos piloto",
                results_and_conclusions_summary="Precisión del 94% en extracción de criterios.",
            ),
            overall_coherence_level="ALTA",
            coherence_findings=[
                CoherenceFinding(
                    alignment_axis="PROBLEMA_OBJETIVOS",
                    status="SOLIDO",
                    analysis="Los objetivos responden directamente al problema formulado.",
                    document_evidence="Sección Planteamiento del problema y Objetivo general.",
                ),
                CoherenceFinding(
                    alignment_axis="OBJETIVOS_METODOLOGIA",
                    status="SOLIDO",
                    analysis="Las fases metodológicas cubren los objetivos específicos.",
                    document_evidence="Sección Metodología iterativa.",
                ),
            ],
            detected_gaps=[
                DefenseGap(
                    thematic_axis="METODOLOGIA",
                    severity="MEDIA",
                    gap_description="No se detalla el criterio de muestreo de los 30 proyectos.",
                    suggested_defense_angle="Preguntar cómo se seleccionaron los proyectos piloto.",
                ),
                DefenseGap(
                    thematic_axis="RESULTADOS",
                    severity="BAJA",
                    gap_description="Falta desglose por modalidad en las métricas reportadas.",
                    suggested_defense_angle="Indagar desempeño diferenciado entre FDC-124 y FDC-125.",
                ),
                DefenseGap(
                    thematic_axis="FUNDAMENTACION",
                    severity="MEDIA",
                    gap_description="Escasa comparación con rúbricas de otras facultades.",
                    suggested_defense_angle="Justificar ponderaciones de la rúbrica institucional.",
                ),
            ],
        )
        return extraction, ExecutionMetrics(latency_ms=42, input_tokens=1200, output_tokens=450)


@pytest.fixture
def fake_analyzer() -> FakeAiAnalyzer:
    return FakeAiAnalyzer()


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        DATABASE_URL="sqlite:///:memory:",
        DB_AUTO_CREATE=True,
        GEMINI_API_KEY="",
        FDC_STORAGE_DIR=tmp_path,
        FDC_MAX_UPLOAD_MB=20,
        FDC_MIN_TEXT_CHARS=500,
    )


@pytest.fixture
def container(test_settings: Settings, fake_analyzer: FakeAiAnalyzer) -> Container:
    cont = Container(settings=test_settings, analyzer=fake_analyzer)
    cont.init_db()
    return cont


@pytest.fixture
def recorded_events(container: Container) -> list[object]:
    events: list[object] = []
    container.event_bus.subscribe(FdcDocumentAnalyzedEvent, events.append)
    container.event_bus.subscribe(FdcIngestionFailedEvent, events.append)
    return events


@pytest.fixture
def client(container: Container) -> TestClient:
    app = FastAPI()
    register_fdc_module(app, container=container)
    return TestClient(app)
