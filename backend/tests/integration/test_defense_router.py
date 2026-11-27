"""Pruebas de integración del flujo completo /api/v1/defense/* y exportación de actas."""
import io
from pathlib import Path
from uuid import uuid4

import docx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.container import Container
from app.core.settings import Settings
from tests.conftest import FDC_125_LINES, FakeAiAnalyzer, build_pdf
from tests.defense_fakes import FakeDefenseDialogAdapter, FakeSttAdapter, FakeTtsAdapter
from app.presentation.app_factory import register_fdc_module


def _upload_fdc_125(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/fdc/upload",
        files={"file": ("informe.pdf", build_pdf(FDC_125_LINES), "application/pdf")},
        data={"fdc_type": "FDC_125"},
    )
    assert resp.status_code == 201
    return resp.json()["document_id"]


def test_complete_four_question_defense_flow_with_tts_audio_and_text(
    client: TestClient,
    fake_stt_adapter: FakeSttAdapter,
    fake_tts_adapter: FakeTtsAdapter,
) -> None:
    doc_id = _upload_fdc_125(client)
    create_resp = client.post(
        "/api/v1/defense/sessions",
        json={"fdc_document_id": doc_id, "jury_profile": "ESTANDAR_UTS"},
    )
    assert create_resp.status_code == 201
    session = create_resp.json()
    sid = session["session_id"]
    assert session["state"] == "AURA_SPEAKING"
    assert session["total_questions"] == 4
    assert "TutoIA" in session["custom_vocabulary"]

    incomplete_report = client.get(f"/api/v1/defense/sessions/{sid}/report?format=pdf")
    assert incomplete_report.status_code == 409
    assert incomplete_report.json()["code"] == "DEFENSE_SESSION_NOT_COMPLETED"

    for q_idx in range(4):
        tts_resp = client.post(f"/api/v1/defense/sessions/{sid}/tts")
        assert tts_resp.status_code == 200
        assert tts_resp.headers["content-type"] == "audio/wav"
        assert tts_resp.content.startswith(b"RIFF")

        if q_idx == 0:
            turn_resp = client.post(
                f"/api/v1/defense/sessions/{sid}/turns/audio",
                files={"audio": ("respuesta.webm", b"FAKE_WEBM_AUDIO", "audio/webm")},
            )
            assert fake_stt_adapter.calls[0]["custom_vocabulary"] == session["custom_vocabulary"]
        else:
            turn_resp = client.post(
                f"/api/v1/defense/sessions/{sid}/turns/text",
                json={"text": "Explicamos los referentes, el metodo y los resultados obtenidos en las UTS."},
            )
        assert turn_resp.status_code == 200
        body = turn_resp.json()
        if q_idx < 3:
            assert body["is_completed"] is False
            assert body["state"] == "AURA_SPEAKING"
            assert body["current_question_index"] == q_idx + 1
        else:
            assert body["is_completed"] is True
            assert body["state"] == "COMPLETED"
            assert body["overall_score"] >= 3.0
            assert body["final_summary"]["verdict"] == "APROBADO"
            averages = body["final_summary"]["criteria_averages"]
            assert set(averages.keys()) == {"pertinencia", "coherencia", "fundamentacion", "metodologia"}
            assert all(0.0 < averages[k] <= 5.0 for k in averages)
            expected_overall = round(
                averages["pertinencia"] * 0.30
                + averages["coherencia"] * 0.25
                + averages["fundamentacion"] * 0.25
                + averages["metodologia"] * 0.20,
                2,
            )
            assert body["overall_score"] == expected_overall

    assert len(fake_tts_adapter.calls) == 4
    hydrated = client.get(f"/api/v1/defense/sessions/{sid}").json()
    assert hydrated["state"] == "COMPLETED"
    assert len(hydrated["turns"]) == 4
    assert hydrated["final_summary"]["criteria_averages"] == body["final_summary"]["criteria_averages"]

    blocked_turn = client.post(
        f"/api/v1/defense/sessions/{sid}/turns/text",
        json={"text": "Intento fuera de estado terminal."},
    )
    assert blocked_turn.status_code == 409
    assert blocked_turn.json()["code"] == "DEFENSE_INVALID_STATE_TRANSITION"

    blocked_tts = client.post(f"/api/v1/defense/sessions/{sid}/tts")
    assert blocked_tts.status_code == 409

    pdf_resp = client.get(f"/api/v1/defense/sessions/{sid}/report?format=pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert ".pdf" in pdf_resp.headers["content-disposition"]
    assert pdf_resp.content.startswith(b"%PDF-")

    docx_resp = client.get(f"/api/v1/defense/sessions/{sid}/report?format=docx")
    assert docx_resp.status_code == 200
    assert (
        docx_resp.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert ".docx" in docx_resp.headers["content-disposition"]
    exported_doc = docx.Document(io.BytesIO(docx_resp.content))
    assert any("Pertinencia" in cell.text for t in exported_doc.tables for r in t.rows for cell in r.cells)

    missing_resp = client.get(f"/api/v1/defense/sessions/{uuid4()}/report?format=pdf")
    assert missing_resp.status_code == 404


def test_follow_up_question_happens_at_most_once_per_base_question(tmp_path: Path) -> None:
    settings = Settings(
        DATABASE_URL="sqlite:///:memory:",
        DB_AUTO_CREATE=True,
        GEMINI_API_KEY="",
        FDC_STORAGE_DIR=tmp_path,
    )
    cont = Container(
        settings=settings,
        analyzer=FakeAiAnalyzer(),
        dialog_adapter=FakeDefenseDialogAdapter(weak_first_turn=True),
        tts_adapter=FakeTtsAdapter(),
        stt_adapter=FakeSttAdapter(),
    )
    cont.init_db()
    app = FastAPI()
    register_fdc_module(app, container=cont)
    local_client = TestClient(app)

    doc_id = _upload_fdc_125(local_client)
    sid = local_client.post(
        "/api/v1/defense/sessions",
        json={"fdc_document_id": doc_id, "jury_profile": "TECNICO_RIGUROSO"},
    ).json()["session_id"]

    # Pregunta 0 (respuesta débil) -> dispara 1 contrapregunta manteniendo question_index=0
    t1 = local_client.post(
        f"/api/v1/defense/sessions/{sid}/turns/text",
        json={"text": "Respuesta muy general sin metricas concretas del proyecto."},
    ).json()
    assert t1["is_follow_up_pending"] is True
    assert t1["current_question_index"] == 0
    assert t1["evaluated_turn"]["needs_follow_up"] is True

    # Contrapregunta 0 (vuelve a ser débil) -> NO dispara segunda contrapregunta, avanza a pregunta 1
    t2 = local_client.post(
        f"/api/v1/defense/sessions/{sid}/turns/text",
        json={"text": "Sigo sin recordar exactamente cual fue la metrica final."},
    ).json()
    assert t2["evaluated_turn"]["is_follow_up"] is True
    assert t2["evaluated_turn"]["needs_follow_up"] is False
    assert t2["is_follow_up_pending"] is False
    assert t2["current_question_index"] == 1

    # Completa las 3 preguntas restantes
    for _ in range(3):
        last = local_client.post(
            f"/api/v1/defense/sessions/{sid}/turns/text",
            json={"text": "Argumentamos los referentes teoricos, diseño y validacion realizada."},
        ).json()
    assert last["is_completed"] is True
    hydrated = local_client.get(f"/api/v1/defense/sessions/{sid}").json()
    assert len(hydrated["turns"]) == 5
