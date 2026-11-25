"""Pruebas de integración de endpoints /api/v1/fdc/*."""
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.container import Container
from app.core.settings import Settings
from app.domain.events.fdc_events import FdcDocumentAnalyzedEvent
from app.presentation.app_factory import register_fdc_module
from tests.conftest import FDC_124_LINES, FDC_125_LINES, build_docx, build_pdf


def test_upload_valid_fdc_125_pdf_and_get_by_id(
    client: TestClient,
    container: Container,
    recorded_events: list[object],
) -> None:
    pdf_bytes = build_pdf(FDC_125_LINES)
    resp = client.post(
        "/api/v1/fdc/upload",
        files={"file": ("informe_final.pdf", pdf_bytes, "application/pdf")},
        data={"fdc_type": "FDC_125", "academic_program": "Ingeniería de Sistemas"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["fdc_type"] == "FDC_125"
    assert body["analysis"]["strategy_name"] == "Fdc125FinalReportStrategy"
    assert body["analysis"]["model_name"] == "fake-model"
    assert len(body["analysis"]["detected_gaps"]) == 3
    assert len(list((container.settings.FDC_STORAGE_DIR / "fdc_uploads").glob("*.pdf"))) == 1
    assert any(isinstance(ev, FdcDocumentAnalyzedEvent) for ev in recorded_events)

    get_resp = client.get(f"/api/v1/fdc/{body['document_id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["document_id"] == body["document_id"]


def test_get_nonexistent_document_returns_404(client: TestClient) -> None:
    resp = client.get(f"/api/v1/fdc/{uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["code"] == "FDC_DOCUMENT_NOT_FOUND"


def test_upload_oversized_file_returns_413(client: TestClient) -> None:
    oversized = b"%PDF-" + b"0" * (20 * 1024 * 1024)
    resp = client.post(
        "/api/v1/fdc/upload",
        files={"file": ("grande.pdf", oversized, "application/pdf")},
        data={"fdc_type": "FDC_125"},
    )
    assert resp.status_code == 413
    assert resp.json()["code"] == "FDC_FILE_TOO_LARGE"


def test_upload_invalid_extension_returns_415(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/fdc/upload",
        files={"file": ("archivo.txt", b"contenido de prueba", "text/plain")},
        data={"fdc_type": "FDC_125"},
    )
    assert resp.status_code == 415
    assert resp.json()["code"] == "FDC_UNSUPPORTED_FORMAT"


def test_upload_fdc_124_content_as_125_returns_422_with_missing_sections(
    client: TestClient,
) -> None:
    resp = client.post(
        "/api/v1/fdc/upload",
        files={"file": ("propuesta.pdf", build_pdf(FDC_124_LINES), "application/pdf")},
        data={"fdc_type": "FDC_125"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "FDC_INVALID_STRUCTURE"
    assert body["context"]["missing_sections"] == ["conclusiones", "resultados"]


def test_upload_valid_docx_as_fdc_124_returns_201(client: TestClient) -> None:
    docx_bytes = build_docx(FDC_124_LINES)
    resp = client.post(
        "/api/v1/fdc/upload",
        files={
            "file": (
                "propuesta.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={"fdc_type": "FDC_124", "modality": "DESARROLLO_TECNOLOGICO"},
    )
    assert resp.status_code == 201
    assert resp.json()["analysis"]["strategy_name"] == "Fdc124ProposalStrategy"


def test_real_gemini_adapter_without_api_key_returns_503(tmp_path: Path) -> None:
    settings = Settings(
        DATABASE_URL="sqlite:///:memory:",
        DB_AUTO_CREATE=True,
        GEMINI_API_KEY="",
        FDC_STORAGE_DIR=tmp_path,
    )
    real_container = Container(settings=settings)
    app = FastAPI()
    register_fdc_module(app, container=real_container)
    real_client = TestClient(app)

    resp = real_client.post(
        "/api/v1/fdc/upload",
        files={"file": ("informe.pdf", build_pdf(FDC_125_LINES), "application/pdf")},
        data={"fdc_type": "FDC_125"},
    )
    assert resp.status_code == 503
    assert resp.json()["code"] == "AI_PROVIDER_NOT_CONFIGURED"
