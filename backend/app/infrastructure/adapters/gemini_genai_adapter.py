"""Adaptador de infraestructura para Google Gemini (google-genai SDK)."""
from datetime import datetime, timedelta, timezone
import io
import time

from pydantic import ValidationError

from app.domain.entities.fdc_analysis import (
    AcademicSynthesis,
    CoherenceFinding,
    DefenseGap,
    ExecutionMetrics,
    FdcExtraction,
)
from app.domain.entities.fdc_document import Modality
from app.domain.entities.project import Author
from app.domain.exceptions.fdc_exceptions import (
    AiProviderNotConfiguredError,
    AiProviderUnavailableError,
    AiResponseValidationError,
    FdcDomainError,
)
from app.domain.ports.ai_fdc_analyzer_port import RemoteFileRef
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy
from app.infrastructure.adapters.gemini_fdc_schema import FdcGeminiExtractionSchema


class GeminiGenAiAdapter:
    """Implementa AiFdcAnalyzerPort sobre google-genai Files API + Interactions."""

    def __init__(self, api_key: str, model: str, timeout_seconds: int = 120) -> None:
        self._api_key = api_key.strip()
        self.model_name = model.strip()
        self._timeout_seconds = timeout_seconds

    def _http_options(self):
        from google.genai import types

        return types.HttpOptions(
            timeout=self._timeout_seconds * 1000,
            retry_options=types.HttpRetryOptions(attempts=1),
        )

    def _client(self):
        if not self._api_key:
            raise AiProviderNotConfiguredError(
                message="GEMINI_API_KEY no está configurada en el entorno del backend.",
                context={"model": self.model_name},
            )
        from google import genai

        return genai.Client(api_key=self._api_key, http_options=self._http_options())

    def upload_document(
        self,
        content: bytes,
        mime_type: str,
        display_name: str,
        extracted_text: str,
    ) -> RemoteFileRef:
        """Sube PDF nativo o texto normalizado de DOCX a Gemini Files API."""
        client = self._client()
        if mime_type == "application/pdf":
            upload_bytes = content
            upload_mime = mime_type
        else:
            upload_bytes = extracted_text.encode("utf-8")
            upload_mime = "text/plain"

        try:
            uploaded = client.files.upload(
                file=io.BytesIO(upload_bytes),
                config={"mime_type": upload_mime, "display_name": display_name},
            )
            expires_at = getattr(uploaded, "expiration_time", None) or (
                datetime.now(timezone.utc) + timedelta(hours=48)
            )
            return RemoteFileRef(
                name=uploaded.name or "",
                uri=uploaded.uri or "",
                mime_type=getattr(uploaded, "mime_type", None) or upload_mime,
                expires_at=expires_at,
            )
        except FdcDomainError:
            raise
        except Exception as exc:
            raise AiProviderUnavailableError(
                message="No fue posible subir el documento a Gemini Files API.",
                context={
                    "reason": str(exc),
                    "status_code": self._extract_status_code(exc),
                    "error_type": type(exc).__name__,
                },
            ) from exc

    def analyze(
        self,
        file_ref: RemoteFileRef,
        strategy: FdcAnalysisStrategy,
        model_override: str | None = None,
    ) -> tuple[FdcExtraction, ExecutionMetrics]:
        """Solicita Structured Output validado con Pydantic mediante Interactions API."""
        client = self._client()
        active_model = (model_override or self.model_name).strip()
        started = time.perf_counter()
        try:
            interaction = client.interactions.create(
                model=active_model,
                system_instruction=strategy.build_system_instruction(),
                input=[
                    {
                        "type": "document",
                        "uri": file_ref.uri,
                        "mime_type": file_ref.mime_type,
                    },
                    {"type": "text", "text": strategy.build_analysis_prompt()},
                ],
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": FdcGeminiExtractionSchema.model_json_schema(),
                },
                timeout=float(self._timeout_seconds),
            )
            parsed = FdcGeminiExtractionSchema.model_validate_json(interaction.output_text or "")
        except ValidationError as exc:
            raise AiResponseValidationError(
                message="La respuesta estructurada de Gemini no cumplió el esquema FDC esperado.",
                context={"errors": exc.errors(), "model": active_model},
            ) from exc
        except FdcDomainError:
            raise
        except Exception as exc:
            raise AiProviderUnavailableError(
                message="Error al analizar el documento con Google Gemini.",
                context={
                    "reason": str(exc),
                    "model": active_model,
                    "status_code": self._extract_status_code(exc),
                    "error_type": type(exc).__name__,
                },
            ) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        usage = getattr(interaction, "usage", None)
        metrics = ExecutionMetrics(
            latency_ms=latency_ms,
            input_tokens=getattr(usage, "total_input_tokens", None),
            output_tokens=getattr(usage, "total_output_tokens", None),
            model_used=active_model,
        )
        return self._to_domain(parsed), metrics

    @staticmethod
    def _extract_status_code(exc: Exception) -> int | None:
        raw = getattr(exc, "status_code", None)
        if isinstance(raw, int):
            return raw
        code = getattr(exc, "code", None)
        return code if isinstance(code, int) else None

    @staticmethod
    def _to_domain(parsed: FdcGeminiExtractionSchema) -> FdcExtraction:
        synthesis = AcademicSynthesis(
            central_problem=parsed.problem.central_problem,
            research_question=parsed.problem.research_question,
            justification_summary=parsed.problem.justification_summary,
            general_objective=parsed.objectives.general_objective,
            specific_objectives=parsed.objectives.specific_objectives,
            research_type_and_approach=parsed.methodology.research_type_and_approach,
            phases_or_stages=parsed.methodology.phases_or_stages,
            technologies_and_instruments=parsed.methodology.technologies_and_instruments,
            validation_scope=parsed.methodology.validation_scope,
            results_and_conclusions_summary=parsed.results_and_conclusions_summary,
        )
        findings = [
            CoherenceFinding(
                alignment_axis=item.alignment_axis,
                status=item.status,
                analysis=item.analysis,
                document_evidence=item.document_evidence,
            )
            for item in parsed.coherence_findings
        ]
        gaps = [
            DefenseGap(
                thematic_axis=item.thematic_axis,
                severity=item.severity,
                gap_description=item.gap_description,
                suggested_defense_angle=item.suggested_defense_angle,
            )
            for item in parsed.detected_gaps_for_defense
        ]
        authors = [
            Author(full_name=a.full_name, student_code=a.student_code)
            for a in parsed.authors
        ]
        return FdcExtraction(
            title=parsed.title,
            authors=authors,
            director_name=parsed.director_name,
            detected_academic_program=parsed.detected_academic_program,
            detected_modality=Modality(parsed.detected_modality),
            synthesis=synthesis,
            overall_coherence_level=parsed.overall_coherence_level,
            coherence_findings=findings,
            detected_gaps=gaps,
        )
