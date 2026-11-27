"""Prueba de integración del registro en el main.py legacy."""
from app.main import app


def test_legacy_app_exposes_v1_fdc_and_defense_routes() -> None:
    openapi_paths = set(app.openapi()["paths"].keys())
    assert "/api/v1/fdc/upload" in openapi_paths
    assert "/api/v1/fdc/{document_id}" in openapi_paths
    assert "/api/v1/defense/sessions" in openapi_paths
    assert "/api/v1/defense/sessions/{session_id}" in openapi_paths
    assert "/api/v1/defense/sessions/{session_id}/tts" in openapi_paths
    assert "/api/v1/defense/sessions/{session_id}/turns/audio" in openapi_paths
    assert "/api/v1/defense/sessions/{session_id}/turns/text" in openapi_paths
    assert "/api/health" in openapi_paths
