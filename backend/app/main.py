"""
Tutoia · API orquestadora de la sustentación inteligente.

Exposición FastAPI del ciclo completo:
1.  Crear sesión de sustentación (estudiante, tema, resumen, alcance).
2.  Iniciar → AURA presenta su guion y formula la primera pregunta.
3.  Responder → análisis en caliente + siguiente turno adaptativo.
4.  Acta de evaluación autocontenida (gráficas SVG, lista para PDF).

El frontend vive en ``/frontend`` y se sirve estáticamente desde la misma
API: un solo comando levanta la plataforma completa.
"""
import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
from app.services import dialog, evaluator, llm, report

app = FastAPI(
    title="Tutoia API",
    version=settings.VERSION,
    description=(
        "Plataforma inteligente con avatar evaluador (AURA) para la automatización "
        "de sustentaciones de trabajos de grado mediante PLN · UTS · 2026"
    ),
)

# ── Estado en memoria (MVP): sesiones concurrentes con acceso protegido ──
_MUTEX = threading.Lock()
_SESIONES: dict[str, "Sesion"] = {}

FRONTEND_DIR = settings.PROJECT_ROOT / "frontend" / "dist"


# ═══════════════════════════════════════════════════════════════════
#  Modelo de dominio
# ═══════════════════════════════════════════════════════════════════
@dataclass
class Turno:
    """Intercambio atómico: una pregunta de AURA ↔ su respuesta."""
    indice: int
    tipo: str                      # principal | seguimiento
    eje: str
    eje_etiqueta: str
    pregunta: str
    dificultad: str = "intermedia"
    respuesta: str = ""
    nota_global: float | None = None
    criterios: dict = field(default_factory=dict)
    fortalezas: list = field(default_factory=list)
    oportunidades: list = field(default_factory=list)
    motor: str = ""
    marcas: float = field(default_factory=time.time)


@dataclass
class Sesion:
    """Estado completo de una sustentación en curso."""
    id: str
    estudiante: str
    tema: str
    resumen: str
    enfoque: str = ""
    total_preguntas: int = 6
    estado: str = "creada"         # creada | en_curso | finalizada
    turnos: list = field(default_factory=list)
    pregunta_pendiente: dict | None = None
    ejes_usados: list = field(default_factory=list)
    seguimientos: dict = field(default_factory=dict)   # eje → nº de refuerzos aplicados
    ultima_evaluacion: dict | None = None
    guion_apertura: dict | None = None
    nota_final: float | None = None
    banda_final: str = ""
    acta_archivo: str | None = None
    motor_usado: str = ""
    creada: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════════════════════════
#  Contratos de la API (pydantic)
# ═══════════════════════════════════════════════════════════════════
class SesionRequest(BaseModel):
    estudiante: str = Field(min_length=2, max_length=120, examples=["Ana María Sofán Ruiz"])
    tema: str = Field(min_length=8, max_length=250, examples=["Sistema de tutorías adaptativas con PLN"])
    resumen: str = Field(min_length=40, max_length=6000,
                         examples=["Resumen del trabajo de grado con problema, método y resultados…"])
    enfoque: str = Field(default="", max_length=120)   # p. ej. "Ingeniería de Sistemas"
    total_preguntas: int = Field(default=6, ge=3, le=len(dialog.EJES))


class RespuestaRequest(BaseModel):
    texto: str = Field(min_length=1, max_length=8000)


# ═══════════════════════════════════════════════════════════════════
#  Endpoints · ciclo de vida de la sesión
# ═══════════════════════════════════════════════════════════════════
@app.on_event("startup")
def restaurar_sesiones():
    """
    Recupera las sesiones persistidas tras un reinicio del backend.
    Garantiza que una sustentación no pierda su historial si el proceso
    se levanta de nuevo — requisito de continuidad del evento académico.
    """
    for archivo in settings.SESIONES_DIR.glob("*.json"):
        try:
            datos = json.loads(archivo.read_text(encoding="utf-8"))
            turnos = [Turno(**t) for t in datos.get("turnos", [])]
            sesion = Sesion(
                id=datos["id"], estudiante=datos["estudiante"], tema=datos["tema"],
                resumen=datos["resumen"], enfoque=datos.get("enfoque", ""),
                total_preguntas=datos.get("total_preguntas", 6),
                estado=datos.get("estado", "creada"),
                turnos=turnos,
                pregunta_pendiente=datos.get("pregunta_pendiente"),
                ejes_usados=datos.get("ejes_usados", []),
                seguimientos=datos.get("seguimientos", {}),
                ultima_evaluacion=datos.get("ultima_evaluacion"),
                guion_apertura=datos.get("guion_apertura"),
                nota_final=datos.get("nota_final"),
                banda_final=datos.get("banda_final", ""),
                acta_archivo=datos.get("acta_archivo"),
                motor_usado=datos.get("motor_usado", ""),
                creada=datos.get("creada", time.time()),
            )
            with _MUTEX:
                _SESIONES[sesion.id] = sesion
        except Exception:  # noqa: BLE001 — un archivo corrupto no bloquea el arranque
            continue


@app.get("/api/health", tags=["Sistema"])
def salud() -> dict:
    """Latido del sistema + motor de IA activo (información para el panel)."""
    return {
        "servicio": "Tutoia",
        "version": settings.VERSION,
        "motor": llm.motor_activo(),
        "sesiones_activas": len(_SESIONES),
    }


@app.post("/api/sesiones", tags=["Sustentación"], status_code=201)
def crear_sesion(peticion: SesionRequest) -> dict:
    """Objetivo específico 1 → registra la sesión con los parámetros definidos."""
    sid = uuid.uuid4().hex[:12]
    sesion = Sesion(
        id=sid,
        estudiante=peticion.estudiante.strip(),
        tema=peticion.tema.strip(),
        resumen=peticion.resumen.strip(),
        enfoque=peticion.enfoque.strip(),
        total_preguntas=peticion.total_preguntas,
    )
    with _MUTEX:
        _SESIONES[sid] = sesion
    return {"sesion_id": sid, "estado": sesion.estado, "motor": llm.motor_activo()}


@app.get("/api/sesiones/{sid}", tags=["Sustentación"])
def obtener_sesion(sid: str) -> dict:
    """Estado completo de la sesión para el frontend (historial incluido)."""
    sesion = _obtener(sid)
    datos = asdict(sesion)
    datos["motor"] = llm.motor_activo()
    return datos


@app.post("/api/sesiones/{sid}/iniciar", tags=["Sustentación"])
def iniciar_sesion(sid: str) -> dict:
    """
    Objetivo específico 2 → AURA despliega su guion de apertura y la
    primera pregunta del primer eje temático.
    """
    sesion = _obtener(sid)
    with _MUTEX:
        if sesion.estado == "en_curso" and sesion.pregunta_pendiente:
            return _cuerpo_apertura(sesion)
        if sesion.estado == "finalizada":
            raise HTTPException(409, "Esta sustentación ya fue finalizada.")

        sesion.guion_apertura = dialog.saludo_inicial(
            sesion.estudiante, sesion.tema, sesion.total_preguntas
        )
        siguiente = dialog.decidir_siguiente_turno(sesion)
        if siguiente is None:  # defensa: sesión con total_preguntas inválido
            raise HTTPException(500, "La configuración de la sesión no permite preguntas.")
        sesion.pregunta_pendiente = siguiente
        sesion.motor_usado = llm.motor_activo()
        sesion.estado = "en_curso"
        _persistir(sesion)

    return _cuerpo_apertura(sesion)


@app.post("/api/sesiones/{sid}/responder", tags=["Sustentación"])
def responder(sid: str, peticion: RespuestaRequest) -> dict:
    """
    Objetivo específico 3 → núcleo del producto:
    analiza la respuesta en caliente, pondera la rúbrica y genera el
    turno siguiente (retro-pregunta o avance de eje) con AURA.
    """
    sesion = _obtener(sid)
    with _MUTEX:
        if sesion.estado != "en_curso" or not sesion.pregunta_pendiente:
            raise HTTPException(409, "No hay pregunta pendiente para esta sesión.")

        texto = peticion.texto.strip()
        if len(texto.split()) < settings.MIN_RESPUESTA_PALABRAS:
            raise HTTPException(
                422,
                f"La respuesta es demasiado corta: AURA necesita al menos "
                f"{settings.MIN_RESPUESTA_PALABRAS} palabras para analizarla.",
            )

        pendiente = sesion.pregunta_pendiente
        turno = Turno(
            indice=len(sesion.turnos) + 1,
            tipo=pendiente["tipo"],
            eje=pendiente["eje"],
            eje_etiqueta=pendiente["eje_etiqueta"],
            pregunta=pendiente["texto"],
            dificultad=pendiente.get("dificultad", "intermedia"),
            respuesta=texto,
            motor=llm.motor_activo(),
        )

        evaluacion = evaluator.evaluar_respuesta(turno, texto, sesion.tema, sesion.resumen)
        turno.nota_global = evaluacion["nota_global"]
        turno.criterios = evaluacion["criterios"]
        turno.fortalezas = evaluacion["fortalezas"]
        turno.oportunidades = evaluacion["oportunidades"]
        turno.motor = evaluacion["motor"]
        sesion.motor_usado = evaluacion["motor"]

        sesion.ultima_evaluacion = evaluacion
        sesion.turnos.append(turno)
        siguiente = dialog.decidir_siguiente_turno(sesion)
        sesion.pregunta_pendiente = siguiente
        if siguiente is None:
            sesion.estado = "finalizada"

        _persistir(sesion)

    return {
        "evaluacion": {
            "nota_global": turno.nota_global,
            "criterios": turno.criterios,
            "fortalezas": turno.fortalezas,
            "oportunidades": turno.oportunidades,
            "motor": evaluacion["motor"],
        },
        "siguiente": siguiente,
        "cierre": siguiente is None,
        "turno": _turno_publico(turno),
    }


@app.post("/api/sesiones/{sid}/acta", tags=["Sustentación"])
def generar_acta(sid: str) -> dict:
    """Objetivo específico 4 → consolida la nota y emite el acta imprimible."""
    sesion = _obtener(sid)
    with _MUTEX:
        if sesion.nota_final is None:
            if not sesion.turnos:
                raise HTTPException(409, "No hay respuestas evaluadas todavía.")
            medias = _medias_por_criterio(sesion)
            sesion.nota_final = evaluator.nota_ponderada(medias)
            banda, _ = evaluator.banda_de(sesion.nota_final)
            sesion.banda_final = banda
            _persistir(sesion)

        if sesion.acta_archivo is None:
            ruta = report.generar_acta(sesion)
            sesion.acta_archivo = ruta.name
            _persistir(sesion)

    return {
        "nota_final": sesion.nota_final,
        "banda": sesion.banda_final,
        "guion_cierre": dialog.guion_cierre(sesion.estudiante, sesion.nota_final, sesion.banda_final),
        "acta_url": f"/api/reportes/{sesion.acta_archivo}",
    }


@app.get("/api/reportes/{archivo}", tags=["Sustentación"])
def servir_acta(archivo: str):
    """Entrega un acta ya generada (HTML autocontenido)."""
    if "/" in archivo or "\\" in archivo or ".." in archivo:
        raise HTTPException(400, "Nombre de archivo inválido.")
    ruta = settings.REPORTES_DIR / archivo
    if not ruta.is_file():
        raise HTTPException(404, "Acta no encontrada.")
    return FileResponse(ruta, media_type="text/html")


@app.get("/api/rubrica", tags=["Sistema"])
def ver_rubrica() -> dict:
    """Rúbrica institucional integrada (transparencia para jurados y desarrollo)."""
    return {
        "criterios": [
            {"codigo": c["codigo"], "etiqueta": c["etiqueta"], "peso": c["peso"],
             "descriptor": c["descriptor"]}
            for c in evaluator.CRITERIOS
        ],
        "bandas": evaluator.BANDAS,
        "ejes": [{"codigo": e["codigo"], "etiqueta": e["etiqueta"]} for e in dialog.EJES],
    }


# ═══════════════════════════════════════════════════════════════════
#  Servicios internos
# ═══════════════════════════════════════════════════════════════════
def _cuerpo_apertura(sesion: Sesion) -> dict:
    """Cuerpo único de respuesta del arranque (idempotente entre ramas)."""
    return {
        "tema": sesion.tema,
        "estudiante": sesion.estudiante,
        "enfoque": sesion.enfoque,
        "total_preguntas": sesion.total_preguntas,
        "motor": sesion.motor_usado or llm.motor_activo(),
        "apertura": sesion.guion_apertura,
        "turno": sesion.pregunta_pendiente,
    }


def _obtener(sid: str) -> Sesion:
    with _MUTEX:
        sesion = _SESIONES.get(sid)
    if sesion is None:
        raise HTTPException(404, "Sesión no encontrada.")
    return sesion


def _medias_por_criterio(sesion: Sesion) -> dict:
    medias = {}
    for crit in evaluator.CRIT_CODIGOS:
        valores = [t.criterios[crit]["puntaje"] for t in sesion.turnos if crit in t.criterios]
        medias[crit] = round(sum(valores) / len(valores), 2) if valores else 0.0
    return medias


def _turno_publico(turno: Turno) -> dict:
    d = asdict(turno)
    d.pop("criterios", None)
    return d


def _persistir(sesion: Sesion) -> None:
    """Volcado JSON de la sesión (trazabilidad + recuperación ante reinicios)."""
    try:
        ruta = settings.SESIONES_DIR / f"{sesion.id}.json"
        ruta.write_text(json.dumps(asdict(sesion), ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass  # el MVP no bloquea la sustentación por fallo de disco


# ═══════════════════════════════════════════════════════════════════
#  Servir el frontend (SPA ligera) — siempre al final del archivo
# ═══════════════════════════════════════════════════════════════════
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
