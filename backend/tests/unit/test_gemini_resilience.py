"""Pruebas unitarias de resiliencia Gemini (Decorator + Backoff + Fallback)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.application.dto.fdc_ingestion_dto import FdcUploadCommand
from app.core.container import Container
from app.core.settings import Settings
from app.domain.entities.fdc_analysis import ExecutionMetrics, FdcExtraction
from app.domain.entities.fdc_document import FdcType
from app.domain.exceptions.fdc_exceptions import (
    AiProviderNotConfiguredError,
    AiProviderUnavailableError,
)
from app.domain.factories.fdc_strategy_factory import FdcStrategyFactory
from app.domain.ports.ai_fdc_analyzer_port import RemoteFileRef
from app.domain.strategies.fdc_analysis_strategy import FdcAnalysisStrategy
from app.infrastructure.adapters.resilient_ai_analyzer import ResilientAiAnalyzer
from tests.conftest import FDC_125_LINES, FakeAiAnalyzer, build_pdf


class ScriptedAiAnalyzer(FakeAiAnalyzer):
    """Doble de prueba que ejecuta respuestas o excepciones programadas por llamada."""

    def __init__(self, script: list[Exception | str], model_name: str = "gemini-3.8-flash") -> None:
        super().__init__()
        self.model_name = model_name
        self._script = list(script)

    def analyze(
        self,
        file_ref: RemoteFileRef,
        strategy: FdcAnalysisStrategy,
        model_override: str | None = None,
    ) -> tuple[FdcExtraction, ExecutionMetrics]:
        active = model_override or self.model_name
        outcome = self._script.pop(0)
        if isinstance(outcome, Exception):
            self.analyze_calls.append({"uri": file_ref.uri, "strategy": strategy.name, "model": active})
            raise outcome
        extraction, metrics = super().analyze(file_ref, strategy, model_override=active)
        return extraction, ExecutionMetrics(
            latency_ms=metrics.latency_ms,
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            model_used=active,
        )


def _file_ref() -> RemoteFileRef:
    return RemoteFileRef(
        name="files/test-ref",
        uri="https://generativelanguage.googleapis.com/v1beta/files/test-ref",
        mime_type="application/pdf",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
    )


def test_settings_parses_fallback_models_without_duplicating_primary() -> None:
    settings = Settings(
        GEMINI_ANALYSIS_MODEL="gemini-3.8-flash",
        GEMINI_FALLBACK_MODELS=" gemini-3.8-flash , gemini-3.5-flash-lite, , gemini-2.5-flash , gemini-3.5-flash-lite ",
    )
    assert settings.gemini_fallback_models == ["gemini-3.5-flash-lite", "gemini-2.5-flash"]


def test_retry_succeeds_after_transient_503() -> None:
    sleeps: list[float] = []
    inner = ScriptedAiAnalyzer([
        AiProviderUnavailableError("503 service_unavailable: high demand", context={"status_code": 503}),
        "OK",
    ])
    decorator = ResilientAiAnalyzer(
        inner=inner,
        fallback_models=["gemini-3.5-flash-lite"],
        max_retries=2,
        base_delay_seconds=1.5,
        sleep_fn=sleeps.append,
        jitter_fn=lambda _a, _b: 0.1,
    )
    ref = _file_ref()
    _, metrics = decorator.analyze(ref, FdcStrategyFactory.create(FdcType.FDC_125))

    assert metrics.model_used == "gemini-3.8-flash"
    assert sleeps == [1.6]
    assert len(inner.upload_calls) == 0
    assert [c["model"] for c in inner.analyze_calls] == ["gemini-3.8-flash", "gemini-3.8-flash"]


def test_fallback_to_secondary_model_after_primary_exhausts_503_and_429() -> None:
    sleeps: list[float] = []
    inner = ScriptedAiAnalyzer([
        AiProviderUnavailableError("503 service_unavailable", context={"status_code": 503}),
        AiProviderUnavailableError("429 resource_exhausted", context={"status_code": 429}),
        AiProviderUnavailableError("503 high demand", context={"status_code": 503}),
        "OK",
    ])
    decorator = ResilientAiAnalyzer(
        inner=inner,
        fallback_models=["gemini-3.5-flash-lite", "gemini-2.5-flash"],
        max_retries=2,
        base_delay_seconds=1.0,
        sleep_fn=sleeps.append,
        jitter_fn=lambda _a, _b: 0.0,
    )
    ref = _file_ref()
    _, metrics = decorator.analyze(ref, FdcStrategyFactory.create(FdcType.FDC_125))

    assert metrics.model_used == "gemini-3.5-flash-lite"
    assert sleeps == [1.0, 2.0]
    assert [c["model"] for c in inner.analyze_calls] == [
        "gemini-3.8-flash",
        "gemini-3.8-flash",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
    ]
    assert all(c["uri"] == ref.uri for c in inner.analyze_calls)


def test_404_model_not_found_triggers_immediate_fallback_without_retries() -> None:
    sleeps: list[float] = []
    inner = ScriptedAiAnalyzer([
        AiProviderUnavailableError("404 model not found", context={"status_code": 404}),
        "OK",
    ])
    decorator = ResilientAiAnalyzer(
        inner=inner,
        fallback_models=["gemini-3.5-flash-lite"],
        max_retries=2,
        base_delay_seconds=1.5,
        sleep_fn=sleeps.append,
        jitter_fn=lambda _a, _b: 0.0,
    )
    _, metrics = decorator.analyze(_file_ref(), FdcStrategyFactory.create(FdcType.FDC_125))

    assert metrics.model_used == "gemini-3.5-flash-lite"
    assert sleeps == []
    assert [c["model"] for c in inner.analyze_calls] == ["gemini-3.8-flash", "gemini-3.5-flash-lite"]


@pytest.mark.parametrize(
    "exc",
    [
        AiProviderUnavailableError("401 UNAUTHENTICATED: invalid api key", context={"status_code": 401}),
        AiProviderUnavailableError("403 PERMISSION_DENIED", context={"status_code": 403}),
        AiProviderUnavailableError("400 INVALID_ARGUMENT: bad request", context={"status_code": 400}),
        AiProviderNotConfiguredError("GEMINI_API_KEY faltante"),
    ],
)
def test_non_retryable_errors_fail_immediately_without_retries_or_fallback(exc: Exception) -> None:
    sleeps: list[float] = []
    inner = ScriptedAiAnalyzer([exc, "OK"])
    decorator = ResilientAiAnalyzer(
        inner=inner,
        fallback_models=["gemini-3.5-flash-lite"],
        max_retries=2,
        base_delay_seconds=1.5,
        sleep_fn=sleeps.append,
        jitter_fn=lambda _a, _b: 0.0,
    )
    with pytest.raises(type(exc)):
        decorator.analyze(_file_ref(), FdcStrategyFactory.create(FdcType.FDC_125))

    assert sleeps == []
    assert len(inner.analyze_calls) == 1


def test_all_models_exhausted_raises_unavailable_with_attempted_models() -> None:
    sleeps: list[float] = []
    err = AiProviderUnavailableError("503 service_unavailable", context={"status_code": 503})
    inner = ScriptedAiAnalyzer([err, err, err, err])
    decorator = ResilientAiAnalyzer(
        inner=inner,
        fallback_models=["gemini-3.5-flash-lite"],
        max_retries=1,
        base_delay_seconds=1.0,
        sleep_fn=sleeps.append,
        jitter_fn=lambda _a, _b: 0.0,
    )
    with pytest.raises(AiProviderUnavailableError) as exc_info:
        decorator.analyze(_file_ref(), FdcStrategyFactory.create(FdcType.FDC_125))

    assert exc_info.value.context["attempted_models"] == ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
    assert "gemini-3.8-flash" in exc_info.value.message
    assert "gemini-3.5-flash-lite" in exc_info.value.message
    assert sleeps == [1.0, 1.0]


def test_use_case_persists_actual_fallback_model_name(test_settings: Settings) -> None:
    inner = ScriptedAiAnalyzer([
        AiProviderUnavailableError("503 service_unavailable", context={"status_code": 503}),
        "OK",
    ])
    resilient = ResilientAiAnalyzer(
        inner=inner,
        fallback_models=["gemini-3.5-flash-lite"],
        max_retries=0,
        base_delay_seconds=0.0,
        sleep_fn=lambda _: None,
    )
    cont = Container(settings=test_settings, analyzer=resilient)
    cont.init_db()
    with cont.session_factory() as session:
        facade = cont.fdc_facade(session)
        view = facade.upload(
            FdcUploadCommand(
                filename="informe.pdf",
                content=build_pdf(FDC_125_LINES),
                fdc_type=FdcType.FDC_125,
            )
        )
        assert view.analysis.model_name == "gemini-3.5-flash-lite"
        persisted = facade.get(view.document.id)
        assert persisted.analysis.model_name == "gemini-3.5-flash-lite"
