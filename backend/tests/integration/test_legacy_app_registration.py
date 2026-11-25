"""Prueba de integración del registro en el main.py legacy."""
from app.main import app


def test_legacy_app_exposes_v1_fdc_routes() -> None:
    openapi_paths = set(app.openapi()["paths"].keys())
    assert "/api/v1/fdc/upload" in openapi_paths
    assert "/api/v1/fdc/{document_id}" in openapi_paths
    assert "/api/health" in openapi_paths
