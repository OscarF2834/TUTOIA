"""
Tutoia · Núcleo analítico: puntuación semiautomática alineada con la rúbrica.

El análisis de cada respuesta combina **dos motores complementarios**:

┌────────────────────────┬──────────────────────────────────────────────┐
│ Motor HEURÍSTICO       │ Señales léxicas medibles y trazables:        │
│ (local, siempre activo)│ cobertura léxica del resumen, marcadores     │
│                        │ argumentativos, profundidad, referentes      │
│                        │ teóricos y vocabulario metodológico.         │
│                        │ → Determinista, explicable, sin red.         │
├────────────────────────┼──────────────────────────────────────────────┤
│ Motor LLM (en la nube) │ Juicio semántico del contenido contra la     │
│                        │ rúbrica: pertinencia real del argumento.     │
│                        │ → Rico en matices, requiere API key.         │
└────────────────────────┴──────────────────────────────────────────────┘

Cuando ambos disponibles, el LLM produce el juicio y las señales heurísticas
quedan como trazabilidad («evidencia medible») en la justificación del puntaje:
un jurado humano siempre podrá auditar por qué el sistema asignó cada nota.
"""
import json
import logging
import re

from app.services import llm

logger = logging.getLogger("tutoia.evaluator")

# ═══════════════════════════════════════════════════════════════════
#  Rúbrica institucional (espejo de docs/rubrica_uts.json)
# ═══════════════════════════════════════════════════════════════════
CRITERIOS: list[dict] = [
    {
        "codigo": "pertinencia",
        "etiqueta": "Pertinencia de la respuesta",
        "peso": 0.30,
        "descriptor": (
            "Grado en el que la respuesta se dirige de forma explícita a la pregunta formulada "
            "y al problema real del trabajo de grado."
        ),
    },
    {
        "codigo": "coherencia",
        "etiqueta": "Coherencia y fluidez argumentativa",
        "peso": 0.25,
        "descriptor": (
            "Organización lógica de las ideas, conectores discursivos y capacidad de sostener "
            "un hilo argumental sin contradicciones."
        ),
    },
    {
        "codigo": "fundamentacion",
        "etiqueta": "Fundamentación teórica",
        "peso": 0.25,
        "descriptor": (
            "Uso consciente de referentes conceptuales, autores y evidencias para justificar "
            "las afirmaciones realizadas."
        ),
    },
    {
        "codigo": "metodologia",
        "etiqueta": "Dominio metodológico",
        "peso": 0.20,
        "descriptor": (
            "Dominio del cómo: procedimiento, instrumentos, datos y decisiones técnicas del "
            "proyecto, explicadas con precisión."
        ),
    },
]

CRIT_CODIGOS = [c["codigo"] for c in CRITERIOS]
CRIT_PESOS = {c["codigo"]: c["peso"] for c in CRITERIOS}
CRIT_ETIQUETAS = {c["codigo"]: c["etiqueta"] for c in CRITERIOS}

BANDAS: list[tuple[float, str, str]] = [
    (4.5, "Excelente", "Dominio sobresaliente: argumentación sólida, precisa y bien respaldada."),
    (3.5, "Sobresaliente", "Buen dominio general con observaciones menores de forma o respaldo."),
    (2.5, "Aceptable", "Comprensión parcial del tema: hay vacíos que ameritan precisión."),
    (1.5, "Insuficiente", "Respuesta débil: falta profundidad, respaldo o conexión con la tesis."),
    (0.0, "Crítico", "La respuesta no da luces sobre el eje preguntado; se sugiere orientación."),
]

# ═══════════════════════════════════════════════════════════════════
#  Señales léxicas del motor heurístico (explicables y medibles)
# ═══════════════════════════════════════════════════════════════════
CONECTORES: tuple[str, ...] = (
    "por lo tanto", "porque", "debido a", "en consecuencia", "además",
    "en primer lugar", "en segundo lugar", "finalmente", "por ejemplo",
    "es decir", "sin embargo", "por otra parte", "según", "dado que",
    "como resultado", "estos", "esa", "dicho", "mencionada",
)

PALABRAS_TEORICAS: tuple[str, ...] = (
    "teoría", "teórico", "autor", "autores", "referente", "referentes",
    "marco", "concepto", "modelo", "enfoque", "estudió", "investigación",
    "literatura", "estado del arte", "antecedente", "categoría", "paradigma",
    "postula", "sostiene", "define", "según el autor",
)

PALABRAS_METODOLOGICAS: tuple[str, ...] = (
    "metodología", "método", "encuesta", "entrevista", "muestra", "población",
    "cualitativo", "cuantitativo", "experimento", "algoritmo", "dataset",
    "datos", "entrenamiento", "validación", "prueba", "instrumento",
    "cronograma", "análisis", "implementación", "prototipo", "versión",
    "métrica", "evaluación", "iteración",
)

MARCADORES_VAGUEDAD: tuple[str, ...] = (
    "no sé", "mm", "mmm", "mmm…", "eh", "puede ser", "tal vez", "algo así",
    "no recuerdo", "no estoy seguro",
)

_STOPWORDS: set[str] = {
    "sobre", "entre", "través", "durante", "desde", "hasta", "para", "porque",
    "dentro", "todos", "todas", "estos", "estas", "aquel", "aquella", "donde",
    "cuando", "además", "también", "trabajo", "grado", "tesis", "estudiante",
    "investigación", "estudio", "objetivo", "objetivos", "mediante", "partir",
    "aparece", "respecto", "manera", "forma", "parte", "proyecto", "plataforma",
}


def banda_de(nota: float) -> tuple[str, str]:
    """Convierte una nota (escala 0–5) en (etiqueta_cualitativa, descripción)."""
    for umbral, etiqueta, descripcion in BANDAS:
        if nota >= umbral:
            return etiqueta, descripcion
    return BANDAS[-1][1], BANDAS[-1][2]


def nota_ponderada(puntajes: dict[str, float]) -> float:
    """Promedio ponderado de la rúbrica, redondeado a 2 decimales (escala 0–5)."""
    total = sum(
        max(0.0, min(5.0, float(puntajes.get(c, 0.0)))) * CRIT_PESOS[c]
        for c in CRIT_CODIGOS
    )
    return round(total, 2)


# ═══════════════════════════════════════════════════════════════════
#  Motor heurístico local
# ═══════════════════════════════════════════════════════════════════
def _tokens(texto: str) -> list[str]:
    return re.findall(r"[a-záéíóúüñ]{4,}", texto.lower())


def _cobertura_lexica(texto: str, referencia: str) -> float:
    """Fracción de términos clave del contexto (tema+resumen) que la respuesta retoma.

    El denominador se acota a 14 términos: una sustentación oral bien
    preparada retoma entre 8 y 12 conceptos del resumen; ponderar contra
    TODO el vocabulario del resumen castigaría respuestas buenas.
    """
    claves = [t for t in set(_tokens(referencia)) if t not in _STOPWORDS]
    if not claves:
        return 0.5
    respondidos = set(_tokens(texto))
    cubiertas = sum(1 for c in claves if c in respondidos)
    return min(1.0, cubiertas / min(len(claves), 14))


def _escala(valor: float, maximo: float) -> float:
    """Mapea un valor normalizado [0, valor/maximo] a la escala 0-5 acotada."""
    return round(max(0.0, min(5.0, (valor / maximo) * 5.0)), 1)


def puntuar_heuristico(respuesta: str, tema: str, resumen: str) -> tuple[dict, dict, list, list]:
    """
    Motor heurístico: puntúa los 4 criterios a partir de señales medibles.
    Devuelve (puntajes, justificaciones, fortalezas, oportunidades).
    """
    limpio = (respuesta or "").strip().lower()
    palabras = _tokens(limpio)
    n_palabras = len(palabras)

    if n_palabras == 0:
        return (
            {c: 0.0 for c in CRIT_CODIGOS},
            {c: "La respuesta no contiene material analizable." for c in CRIT_CODIGOS},
            [],
            ["La respuesta no contiene material analizable; se sugiere reformular la pregunta."],
        )

    # — Señales brutas ──────────────────────────────────────────────
    n_conectores = sum(1 for c in CONECTORES if c in limpio)
    n_teoricas = sum(1 for p in PALABRAS_TEORICAS if p in limpio)
    n_metodologicas = sum(1 for p in PALABRAS_METODOLOGICAS if p in limpio)
    n_vaguedad = sum(1 for v in MARCADORES_VAGUEDAD if v in limpio)
    n_cifras = len(re.findall(r"\b\d[\d.,%]*\b", limpio))
    cobertura = _cobertura_lexica(limpio, f"{tema} {resumen}")
    profundidad = min(1.0, n_palabras / 90.0)

    justificaciones: dict[str, str] = {}
    señales: list[str] = []

    # — Criterio 1: pertinencia (cobertura léxica + profundidad + datos) ─
    puntaje = _escala(
        0.45 * cobertura + 0.40 * profundidad + 0.15 * min(1.0, n_cifras / 2.0), 1.0
    )
    if profundidad >= 0.80:            # respuestas desplegadas ganan piso argumental
        puntaje += 0.6
    puntaje -= 0.35 * min(2, n_vaguedad)
    justificaciones["pertinencia"] = (
        f"La respuesta retoma {cobertura:.0%} del vocabulario central del tema y "
        f"alcanza {n_palabras} palabras de desarrollo."
    )
    señales.append(f"cobertura_léxica={cobertura:.2f}; palabras={n_palabras}")

    # — Criterio 2: coherencia (conectores + censura de vaguedad) ───
    puntaje_coherencia = _escala(
        min(1.0, n_conectores / 3.5) * 0.65 + profundidad * 0.35, 1.0
    )
    puntaje_coherencia -= 0.35 * min(3, n_vaguedad)
    puntaje_coherencia = max(0.0, min(5.0, puntaje_coherencia))
    justificaciones["coherencia"] = (
        f"Se registraron {n_conectores} marcadores argumentativos que hilan el discurso."
    )

    # — Criterio 3: fundamentación (referentes + datos) ─────────────
    puntaje_fund = _escala(
        min(1.0, n_teoricas / 2.5) * 0.60 + min(1.0, n_cifras / 2.0) * 0.20 + profundidad * 0.20, 1.0
    )
    justificaciones["fundamentacion"] = (
        f"Se detectaron {n_teoricas} referencias conceptuales y {n_cifras} datos o cifras concretas."
    )

    # — Criterio 4: dominio metodológico (lenguaje técnico) ─────────
    puntaje_met = _escala(
        min(1.0, n_metodologicas / 3.0) * 0.70 + profundidad * 0.30, 1.0
    )
    justificaciones["metodologia"] = (
        f"El vocabulario metodológico aparece {n_metodologicas} veces en el argumento."
    )

    # — Fortalezas y oportunidades, automáticamente narradas ────────
    puntajes = {
        "pertinencia": max(0.0, min(5.0, puntaje)),
        "coherencia": puntaje_coherencia,
        "fundamentacion": puntaje_fund,
        "metodologia": puntaje_met,
    }
    # Piso argumental: una respuesta desplegada (≥25 palabras) siempre
    # aporta material evaluable; el foco penalizador se reserva para la
    # vaguedad real y las respuestas esquivas.
    if n_palabras >= 25:
        puntajes = {k: v + 0.8 for k, v in puntajes.items()}
    puntajes = {c: round(max(0.0, min(5.0, v)), 1) for c, v in puntajes.items()}
    justificaciones = {
        "pertinencia": justificaciones.get("pertinencia", ""),
        "coherencia": justificaciones.get("coherencia", ""),
        "fundamentacion": justificaciones.get("fundamentacion", ""),
        "metodologia": justificaciones.get("metodologia", ""),
    }
    fortalezas, oportunidades = [], []
    for cod in CRIT_CODIGOS:
        detalle = justificaciones[cod]
        puntaje_c = puntajes[cod]
        if puntaje_c >= 3.5:
            fortalezas.append(f"{CRIT_ETIQUETAS[cod]}: {detalle}")
        elif puntaje_c < 2.5:
            oportunidades.append(f"Reforzar {CRIT_ETIQUETAS[cod].lower()} — {detalle}")

    return puntajes, justificaciones, fortalezas, oportunidades


# ═══════════════════════════════════════════════════════════════════
#  Evaluación orquestada (motor doble)
# ═══════════════════════════════════════════════════════════════════
_SISTEMA_EVALUADOR = """Eres el módulo analítico de TUTOIA, plataforma de evaluación de
sustentaciones de trabajo de grado de las Unidades Tecnológicas de Santander.
Tu única función: evaluar la respuesta del estudiante contra la rúbrica
institucional, con rigor y criterio de jurado experto.

Criterios con significado:
· pertinencia    (peso 30%): la respuesta responde EXACTAMENTE la pregunta y conecta con el problema real de la tesis.
· coherencia     (peso 25%): lógica, hilo argumental, sin contradicciones ni divagación.
· fundamentacion (peso 25%): se apoya en referentes, datos o evidencia de SU propia investigación.
· metodologia    (peso 20%): demuestra dominio del cómo: métodos, instrumentos, decisiones técnicas.

Reglas de calificación:
1. Puntajes entre 0 y 5 con un decimal, SIN generosidad inflada ni severidad arbitraria:
   5 = dominio magistral · 4 = sólido · 3 = aceptable con vacíos · 2 = débil · 0-1 = inadecuada.
2. Cada justificación debe citar contenido concreto de la propia respuesta del estudiante.
3. Si la respuesta evasiva no llega a la pregunta, los criterios de pertinencia/bases bajan a ≤ 2.
4. requiere_seguimiento=true SOLO si la respuesta fue débil (algún rubro < 2.5) y amerita
   que el avatar pida aclarar/reforzar ANTES de avanzar de eje temático.

Devueves EXCLUSIVAMENTE este JSON:
{
  "criterios": {
    "pertinencia":    {"puntaje": 0.0, "justificacion": "…"},
    "coherencia":     {"puntaje": 0.0, "justificacion": "…"},
    "fundamentacion": {"puntaje": 0.0, "justificacion": "…"},
    "metodologia":    {"puntaje": 0.0, "justificacion": "…"}
  },
  "requiere_seguimiento": false,
  "fortalezas": ["…"],
  "oportunidades": ["…"]
}"""


def evaluar_respuesta(turno, respuesta: str, tema: str, resumen: str) -> dict:
    """
    Evalúa una respuesta con el motor disponible y devuelve el veredicto
    completo listo para la interfaz de AURA.
    """
    respuesta_limpia = (respuesta or "").strip()

    # ── Acceso directo: motor heurístico SIEMPRE computa señales ───
    puntajes_h, justificaciones_h, fortalezas_h, oportunidades_h = puntuar_heuristico(
        respuesta_limpia, tema, resumen
    )

    # ── Motor LLM (si está vivo) eleva el juicio semántico ─────────
    nombre_motor = "heuristico-local"
    criterios: dict = {}
    requiere_seguimiento = False
    fortalezas = fortalezas_h
    oportunidades = oportunidades_h

    if llm.hay_llm_disponible() and respuesta_limpia:
        usuario = (
            f"TEMA DE GRADO: {tema}\n"
            f"RESUMEN DE LA TESIS:\n{(resumen or 'El estudiante no entregó resumen.')}\n\n"
            f"PREGUNTA DEL JURADO VIRTUAL: {turno.pregunta}\n"
            f"EJE TEMÁTICO: {turno.eje_etiqueta}\n\n"
            f"RESPUESTA DEL ESTUDIANTE:\n{respuesta_limpia}\n\n"
            "Devuelve el JSON de evaluación."
        )
        dict_llm = llm.chat_json(_SISTEMA_EVALUADOR, usuario, temperatura=0.2)

        if dict_llm and isinstance(dict_llm.get("criterios"), dict):
            nombre_motor = "llm-nube"
            bruto = dict_llm["criterios"]
            for cod in CRIT_CODIGOS:
                detalle = bruto.get(cod) or {}
                try:
                    puntaje = round(max(0.0, min(5.0, float(detalle.get("puntaje", 0.0)))), 1)
                except (TypeError, ValueError):
                    puntaje = puntajes_h[cod]
                criterios[cod] = {
                    "etiqueta": CRIT_ETIQUETAS[cod],
                    "peso": CRIT_PESOS[cod],
                    "puntaje": puntaje,
                    "justificacion": str(detalle.get("justificacion", "")).strip()
                    or "Sin observación registrada por el juício semántico.",
                }
                if puntaje < 1.5:
                    criterios[cod]["justificacion"] += (
                        f" [Señal heurística de respaldo: {puntajes_h[cod]}/5]"
                    )
            requiere_seguimiento = bool(dict_llm.get("requiere_seguimiento"))
            fortalezas = [str(f) for f in dict_llm.get("fortalezas", [])] or fortalezas_h
            oportunidades = [str(o) for o in dict_llm.get("oportunidades", [])] or oportunidades_h

    if not criterios:
        # ── Respaldo (o modo mock): veredicto del motor heurístico ────
        criterios = {
            cod: {
                "etiqueta": CRIT_ETIQUETAS[cod],
                "peso": CRIT_PESOS[cod],
                "puntaje": puntajes_h[cod],
                "justificacion": justificaciones_h[cod],
            }
            for cod in CRIT_CODIGOS
        }

    # ── Umbral heurístico de seguimiento cuando el LLM no decidió ──
    if not requiere_seguimiento and nombre_motor == "heuristico-local":
        requiere_seguimiento = min(p["puntaje"] for p in criterios.values()) < 2.5

    return {
        "criterios": criterios,
        "nota_global": nota_ponderada({c: v["puntaje"] for c, v in criterios.items()}),
        "requiere_seguimiento": requiere_seguimiento,
        "fortalezas": fortalezas,
        "oportunidades": oportunidades,
        "motor": nombre_motor,
    }
