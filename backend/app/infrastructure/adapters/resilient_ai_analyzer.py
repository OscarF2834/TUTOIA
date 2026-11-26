"""Decorator de resiliencia con reintento exponencial y fallback de modelos Gemini."""
from collections.abc import Callable
import logging
import random
import time

from app.domain.entities.fdc_analysis import ExecutionMetrics, FdcExtraction
from app.domain.exceptions.fdc_exceptions import (
    AiProviderNotConfiguredError,
    AiProviderUnavailableError,
    AiResponseValidationError,
    FdcDomainError,
)
from app.domain.ports.ai_fdc_analyzer_port import AiFdcAnalyzerPort, RemoteFileRef
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy

logger = logging.getLogger("tutoia.ai.resilience")

_NON_RETRYABLE_STATUS = {400, 401, 403}
_FALLBACK_NOW_STATUS = {404}
_TRANSIENT_STATUS = {429, 500, 502, 503, 504}
_NON_RETRYABLE_MARKERS = (
    "401",
    "403",
    "400",
    "unauthenticated",
    "permission_denied",
    "invalid_argument",
    "api_key_invalid",
    "invalid api key",
    "bad request",
)
_FALLBACK_NOW_MARKERS = ("404", "not_found", "not found", "model_not_found")
_TRANSIENT_MARKERS = (
    "503",
    "429",
    "500",
    "502",
    "504",
    "service_unavailable",
    "unavailable",
    "high demand",
    "overloaded",
    "resource_exhausted",
    "rate limit",
    "too many requests",
    "timeout",
    "timed out",
    "deadline_exceeded",
    "connection",
    "network",
)


class ResilientAiAnalyzer:
    """Decorator sobre AiFdcAnalyzerPort con backoff exponencial y fallback de modelos."""

    def __init__(
        self,
        inner: AiFdcAnalyzerPort,
        fallback_models: list[str],
        max_retries: int = 2,
        base_delay_seconds: float = 1.5,
        sleep_fn: Callable[[float], None] = time.sleep,
        jitter_fn: Callable[[float, float], float] = random.uniform,
    ) -> None:
        self._inner = inner
        self._fallback_models = list(fallback_models)
        self._max_retries = max_retries
        self._base_delay = base_delay_seconds
        self._sleep_fn = sleep_fn
        self._jitter_fn = jitter_fn

    @property
    def model_name(self) -> str:
        """Retorna el modelo principal configurado en el adaptador envuelto."""
        return self._inner.model_name

    def upload_document(
        self,
        content: bytes,
        mime_type: str,
        display_name: str,
        extracted_text: str,
    ) -> RemoteFileRef:
        """Sube el documento reintentando solo fallos transitorios."""
        for attempt in range(self._max_retries + 1):
            try:
                return self._inner.upload_document(content, mime_type, display_name, extracted_text)
            except Exception as exc:
                kind = self._classify_error(exc)
                if kind == "non_retryable" or attempt >= self._max_retries:
                    raise
                logger.warning("Reintentando subida a Files API (%d/%d): %s", attempt + 1, self._max_retries, exc)
                self._sleep_with_backoff(attempt)
        raise AiProviderUnavailableError("No fue posible subir el documento al proveedor IA.")

    def analyze(
        self,
        file_ref: RemoteFileRef,
        strategy: FdcAnalysisStrategy,
        model_override: str | None = None,
    ) -> tuple[FdcExtraction, ExecutionMetrics]:
        """Analiza reutilizando file_ref con reintentos y cambio automático de modelo."""
        candidates = self._candidate_models(model_override)
        started = time.perf_counter()
        last_exc: Exception | None = None

        for model in candidates:
            try:
                return self._analyze_with_retries(file_ref, strategy, model, started)
            except _FallbackNextModel as exc:
                last_exc = exc.cause
                continue

        reason = getattr(last_exc, "message", None) or str(last_exc or "Fallo desconocido")
        status_code = self._extract_status_code(last_exc) if last_exc else None
        raise AiProviderUnavailableError(
            message=(
                "Todos los modelos Gemini fallaron tras reintentos: "
                f"{', '.join(candidates)}. Último error: {reason}"
            ),
            context={
                "attempted_models": candidates,
                "last_error": reason,
                "status_code": status_code,
            },
        ) from last_exc

    def _analyze_with_retries(
        self,
        file_ref: RemoteFileRef,
        strategy: FdcAnalysisStrategy,
        model: str,
        started: float,
    ) -> tuple[FdcExtraction, ExecutionMetrics]:
        for attempt in range(self._max_retries + 1):
            try:
                extraction, inner_metrics = self._inner.analyze(file_ref, strategy, model_override=model)
                total_ms = max(inner_metrics.latency_ms, int((time.perf_counter() - started) * 1000))
                metrics = ExecutionMetrics(
                    latency_ms=total_ms,
                    input_tokens=inner_metrics.input_tokens,
                    output_tokens=inner_metrics.output_tokens,
                    model_used=inner_metrics.model_used or model,
                )
                return extraction, metrics
            except Exception as exc:
                kind = self._classify_error(exc)
                if kind == "non_retryable":
                    raise
                if kind == "fallback_now":
                    logger.warning("Modelo %s no disponible (404); cambiando a respaldo.", model)
                    raise _FallbackNextModel(exc) from exc
                logger.warning("Fallo transitorio en modelo %s (%d/%d): %s", model, attempt + 1, self._max_retries, exc)
                if attempt >= self._max_retries:
                    raise _FallbackNextModel(exc) from exc
                self._sleep_with_backoff(attempt)
        raise _FallbackNextModel(AiProviderUnavailableError("Reintentos agotados"))

    def _candidate_models(self, model_override: str | None) -> list[str]:
        primary = (model_override or self._inner.model_name).strip()
        ordered: list[str] = [primary] if primary else []
        for fallback in self._fallback_models:
            clean = fallback.strip()
            if clean and clean not in ordered:
                ordered.append(clean)
        return ordered

    def _sleep_with_backoff(self, attempt: int) -> None:
        if self._base_delay <= 0:
            return
        jitter = self._jitter_fn(0.0, self._base_delay * 0.25)
        self._sleep_fn(self._base_delay * (2**attempt) + max(0.0, jitter))

    @classmethod
    def _classify_error(cls, exc: Exception) -> str:
        if isinstance(exc, (AiProviderNotConfiguredError, AiResponseValidationError)):
            return "non_retryable"
        status_code = cls._extract_status_code(exc)
        if status_code in _NON_RETRYABLE_STATUS:
            return "non_retryable"
        if status_code in _FALLBACK_NOW_STATUS:
            return "fallback_now"
        if status_code in _TRANSIENT_STATUS:
            return "transient"
        detail = f"{exc} {getattr(exc, 'context', '')}".lower()
        if any(marker in detail for marker in _NON_RETRYABLE_MARKERS):
            return "non_retryable"
        if any(marker in detail for marker in _FALLBACK_NOW_MARKERS):
            return "fallback_now"
        if any(marker in detail for marker in _TRANSIENT_MARKERS):
            return "transient"
        return "transient" if isinstance(exc, AiProviderUnavailableError) else "non_retryable"

    @staticmethod
    def _extract_status_code(exc: Exception) -> int | None:
        if isinstance(exc, FdcDomainError):
            ctx_code = exc.context.get("status_code")
            if isinstance(ctx_code, int):
                return ctx_code
        raw = getattr(exc, "status_code", None)
        if isinstance(raw, int):
            return raw
        code = getattr(exc, "code", None)
        return code if isinstance(code, int) else None


class _FallbackNextModel(Exception):
    """Señal interna para avanzar al siguiente modelo candidato."""

    def __init__(self, cause: Exception) -> None:
        super().__init__(str(cause))
        self.cause = cause
