"""Helper compartido para clientes google-genai y failover rápido."""
from collections.abc import Callable
import logging
import time
from typing import Any, TypeVar

from app.domain.exceptions.fdc_exceptions import (
    AiProviderNotConfiguredError,
    AiProviderUnavailableError,
    AiResponseValidationError,
    FdcDomainError,
)

T = TypeVar("T")
logger = logging.getLogger("tutoia.ai.resilience")

_NON_RETRYABLE_STATUS = {400, 401, 403}
_FALLBACK_NOW_STATUS = {404}
_SATURATED_STATUS = {503, 504}
_TRANSIENT_STATUS = {429, 500, 502}
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
_SATURATED_MARKERS = (
    "503",
    "504",
    "service_unavailable",
    "unavailable",
    "high demand",
    "overloaded",
    "timeout",
    "timed out",
    "deadline_exceeded",
)
_TRANSIENT_MARKERS = (
    "429",
    "500",
    "502",
    "resource_exhausted",
    "rate limit",
    "too many requests",
    "connection",
    "network",
)


def build_gemini_client(api_key: str, timeout_seconds: int, model_hint: str) -> Any:
    """Construye cliente google-genai con timeout explícito y sin reintentos SDK."""
    clean_key = api_key.strip()
    if not clean_key:
        raise AiProviderNotConfiguredError(
            message="GEMINI_API_KEY no está configurada en el entorno del backend.",
            context={"model": model_hint},
        )
    from google import genai
    from google.genai import types

    opts = types.HttpOptions(
        timeout=timeout_seconds * 1000,
        retry_options=types.HttpRetryOptions(attempts=1),
    )
    return genai.Client(api_key=clean_key, http_options=opts)


def extract_status_code(exc: Exception) -> int | None:
    """Extrae código HTTP numérico desde una excepción del SDK o dominio."""
    if isinstance(exc, FdcDomainError):
        ctx_code = exc.context.get("status_code")
        if isinstance(ctx_code, int):
            return ctx_code
    raw = getattr(exc, "status_code", None)
    if isinstance(raw, int):
        return raw
    code = getattr(exc, "code", None)
    return code if isinstance(code, int) else None


def classify_gemini_error(exc: Exception) -> str:
    """Clasifica fallos en non_retryable, fallback_now, saturated o transient."""
    if isinstance(exc, (AiProviderNotConfiguredError, AiResponseValidationError)):
        return "non_retryable"
    status = extract_status_code(exc)
    if status in _NON_RETRYABLE_STATUS:
        return "non_retryable"
    if status in _FALLBACK_NOW_STATUS:
        return "fallback_now"
    if status in _SATURATED_STATUS:
        return "saturated"
    if status in _TRANSIENT_STATUS:
        return "transient"
    detail = f"{exc} {getattr(exc, 'context', '')}".lower()
    if any(m in detail for m in _NON_RETRYABLE_MARKERS):
        return "non_retryable"
    if any(m in detail for m in _FALLBACK_NOW_MARKERS):
        return "fallback_now"
    if any(m in detail for m in _SATURATED_MARKERS):
        return "saturated"
    if any(m in detail for m in _TRANSIENT_MARKERS):
        return "transient"
    return "transient" if isinstance(exc, AiProviderUnavailableError) else "non_retryable"


def execute_with_failover(
    models: list[str],
    max_retries: int,
    base_delay: float,
    fn: Callable[[str], T],
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[T, str]:
    """Ejecuta operación sobre modelos candidatos aplicando fail-fast y backoff."""
    started = time.perf_counter()
    last_exc: Exception | None = None
    for idx, model in enumerate(models):
        for attempt in range(max_retries + 1):
            t0 = time.perf_counter()
            try:
                return fn(model), model
            except Exception as exc:
                kind = classify_gemini_error(exc)
                if kind == "non_retryable":
                    raise
                last_exc = exc
                elapsed_s = time.perf_counter() - t0
                next_model = models[idx + 1] if idx + 1 < len(models) else None
                if kind in ("saturated", "fallback_now") or attempt >= max_retries:
                    logger.warning(
                        "Gemini failover | modelo=%s | http=%s | causa=%s | transcurrido=%.1fs | respaldo=%s",
                        model,
                        extract_status_code(exc) or "n/a",
                        kind,
                        elapsed_s,
                        next_model or "ninguno",
                    )
                    break
                sleep_fn(base_delay * (2**attempt))

    raise AiProviderUnavailableError(
        message=f"Todos los modelos Gemini fallaron: {', '.join(models)}. Último error: {last_exc}",
        context={"attempted_models": models, "last_error": str(last_exc)},
    ) from last_exc
