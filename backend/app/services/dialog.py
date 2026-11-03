"""
Tutoia · Motor de flujo de diálogo del avatar evaluador «AURA».

AURA (Avatar Universitario para la Retroalimentación Académica) conduce la
sustentación con una estrategia generativa de tres capas:

1. **Guion temático progremsivo** — seis ejes que replican la lógica real de
   un jurado: contexto → problema → teoría → método → resultados → aportes.
2. **Indagación adaptativa** — si el análisis de una respuesta detecta
   debilidad (heurístico o del LLM), AURA hace una retro-pregunta de
   aterrizaje sobre el criterio más débil antes de avanzar de eje.
3. **Degradación elegante** — sin LLM, un banco de preguntas plantilla
   parametrizado con el tema de la tesis mantiene la sesión completa.

Todo el lenguaje de AURA se produce en español neutro (colombiano),
cordial-profesional, tal como lo haría un jurado institucional.
"""
import random

from app.services import llm

# ═══════════════════════════════════════════════════════════════════
#  Ejecución temática de la sustentación (alineada con la rúbrica UTS)
# ═══════════════════════════════════════════════════════════════════
EJES: list[dict] = [
    {
        "codigo": "contexto",
        "etiqueta": "Contextualización y motivación",
        "enfoque": (
            "En qué problema real del entorno se enmarca el trabajo, por qué es relevante "
            "y qué motivó (académica o socialmente) desarrollarlo."
        ),
        "plantilla": (
            "Para comenzar: ¿qué problema concreto motivó tu trabajo «{tema_corto}» y por qué "
            "consideras que resolverlo es relevante hoy?"
        ),
    },
    {
        "codigo": "problema",
        "etiqueta": "Problema, propósito y alcance",
        "enfoque": (
            "Formulación del problema, objetivo general y alcance real de lo entregado: "
            "qué sí resolvió el trabajo y qué quedó explícitamente fuera."
        ),
        "plantilla": (
            "Ahora aclárame el alcance: ¿cuál es el propósito central de tu trabajo «{tema_corto}» "
            "y qué parte del problema decidiste NO abarcar?"
        ),
    },
    {
        "codigo": "teoria",
        "etiqueta": "Marco teórico y referentes",
        "enfoque": (
            "Referentes conceptuales y estado del arte: qué teorías, autores o trabajos previos "
            "sustentan las decisiones del proyecto y cómo se contrasta con ellos."
        ),
        "plantilla": (
            "En cuanto al soporte conceptual: ¿qué teorías, autores o trabajos previos "
            "fundamentan tu propuesta «{tema_corto}» y qué los hizo los más adecuados?"
        ),
    },
    {
        "codigo": "metodo",
        "etiqueta": "Metodología y diseño",
        "enfoque": (
            "Alineación problema-método: enfoque, técnicas, instrumentos, datos o insumos, "
            "y justificación de por qué esa vía responde a los objetivos."
        ),
        "plantilla": (
            "Hablemos de la ruta: ¿qué metodología y técnicas usaste para abordar el problema y "
            "por qué esa vía era la correcta para los objetivos de tu trabajo?"
        ),
    },
    {
        "codigo": "resultados",
        "etiqueta": "Resultados y análisis",
        "enfoque": (
            "Hallazgos verificables: qué obtuviste, con qué evidencia lo demuestras y cómo "
            "interpretas esos resultados frente al problema inicial."
        ),
        "plantilla": (
            "Lleguemos a lo concreto: ¿cuáles fueron los resultados principales de tu trabajo y "
            "qué evidencia los respalda frente al problema que planteaste?"
        ),
    },
    {
        "codigo": "aporte",
        "etiqueta": "Conclusiones y aporte",
        "enfoque": (
            "Cierre crítico: conclusiones defendibles con lo mostrado, aportación académica o "
            "práctica, trabajo futuro y lecciones del proceso."
        ),
        "plantilla": (
            "Para cerrar: ¿cuáles son las conclusiones que puedes sostener con lo que hoy has "
            "mostrado, cuál es el aporte real de tu trabajo y qué seguirías investigando?"
        ),
    },
]

# Retro-preguntas de aterrizaje por criterio débil (motor heurístico).
RETRO_PLANTILLAS: dict[str, str] = {
    "pertinencia": (
        "Me interesa precisar eso: ayuda a aterrizar tu respuesta de forma explícita en el "
        "problema de «{tema_corto}»: ¿qué parte exacta del problema estás resolviendo con ello?"
    ),
    "coherencia": (
        "Déjame confirmar que entendí bien: organiza tu respuesta en idea principal → explicación → "
        "ejemplo concreto de tu trabajo. ¿Podrías repetirla en esos tres pasos?"
    ),
    "fundamentacion": (
        "Antes de avanzar, quiero que respaldes esa afirmación: ¿qué referencia conceptual, dato "
        "o trabajo previo de tu marco teórico sustenta lo que acabas de decir?"
    ),
    "metodologia": (
        "Reformulemos desde la evidencia: ¿cómo exactamente lo ejecutaste en tu metodología, "
        "cuál fue el procedimiento que seguiste paso a paso y con qué insumos?"
    ),
}

PENSAMIENTOS: tuple[str, ...] = (
    "Analizando tu argumento…",
    "Contrastando con la rúbrica…",
    "Ponderando la evidencia…",
    "Cotejando con los referentes…",
)


# ═══════════════════════════════════════════════════════════════════
#  Guion conversacional
# ═══════════════════════════════════════════════════════════════════
def saludo_inicial(estudiante: str, tema: str, total_preguntas: int) -> dict:
    """Guion de apertura que AURA pronuncia antes de la primera pregunta."""
    nombre = estudiante.strip() or "estudiante"
    texto = (
        f"Bienvenido, {nombre}. Soy AURA, tu avatar evaluador de las Unidades Tecnológicas de "
        f"Santander. Seré tu acompañante durante esta sustentación sobre «{tema}». "
        f"Tendremos una conversación de unas {total_preguntas} preguntas: un eje por tema central "
        "de tu trabajo. Responde con calma y con evidencia de tu propia investigación. "
        "Cuando estés listo, presiona el botón del micrófono y comienza."
    )
    return {"tipo": "apertura", "texto": texto}


def guion_cierre(estudiante: str, nota: float, banda: str) -> dict:
    """Despedida institucional, sin revelar criterio por criterio."""
    nombre = estudiante.strip() or "estudiante"
    texto = (
        f"Gracias, {nombre}. Se completó la sustentación y registré tu desempeño en cada eje "
        "temático con la rúbrica institucional. Tu evaluación consolidada es de "
        f"{nota:.1f} sobre cinco — {banda}. El acta con el análisis completo ya fue generada y "
        "queda a disposición de tu jurado. Felicitaciones por tu trabajo."
    )
    return {"tipo": "cierre", "texto": texto}


def decidir_siguiente_turno(sesion) -> dict | None:
    """
    Decide y genera el siguiente turno de AURA.

    Lógica de avance:
    · Si la evaluación anterior pidió profundizar Y hay margen → retro-pregunta.
    · Si aún quedan ejes temáticos → siguiente pregunta principal.
    · Si los ejes se agotaron (o se alcanzó el techo) → None (cierre).
    """
    evaluacion = sesion.ultima_evaluacion or {}
    cuestionario_previo = sesion.turnos[-1] if sesion.turnos else None
    realizar_seguimiento = bool(
        evaluacion.get("requiere_seguimiento")
        and cuestionario_previo
        and len(sesion.turnos) < sesion.total_preguntas * 2
        and sesion.ejes_usados
        # Política institucional: máximo 1 refuerzo por eje — la sustentación
        # avanza; el concepto final integrará la debilidad en el acta.
        and sesion.seguimientos.get(cuestionario_previo.eje, 0) < 1
    )

    if realizar_seguimiento and cuestionario_previo:
        sesion.seguimientos[cuestionario_previo.eje] = (
            sesion.seguimientos.get(cuestionario_previo.eje, 0) + 1
        )
        return _pregunta_seguimiento(sesion, cuestionario_previo, evaluacion)

    # ── Avanzar de eje ──────────────────────────────────────────────
    if len(sesion.ejes_usados) >= min(sesion.total_preguntas, len(EJES)):
        return None
    eje = EJES[len(sesion.ejes_usados)]
    sesion.ejes_usados.append(eje["codigo"])

    return _preguntar(sesion, eje, es_seguimiento=False)


# ═══════════════════════════════════════════════════════════════════
#  Generación de preguntas (LLM con respaldo determinista)
# ═══════════════════════════════════════════════════════════════════
_SISTEMA_AURA = """Eres AURA (Avatar Universitario para la Retroalimentación Académica),
la evaluadora virtual institucional de las Unidades Tecnológicas de Santander que
conduce sustentaciones de trabajo de grado junto al jurado.

Reglas inamovibles:
1. Formulas UNA sola pregunta por turno, corta (máximo 40 palabras), clara y en
   español neutro colombiano, con tono cordial-profesional de tribunal académico.
2. La pregunta DEBE anclarse al contenido real de la tesis que te entregan; si el
   estudiante ya respondió algo, la pregunta siguiente profundiza lo escuchado o
   avanza con lógica temática; nunca repites la misma variable que ya se preguntó.
3. Nunca revelas puntajes, notas ni términos de la rúbrica («criterio 3.0», etc.).
4. Nunca inventas datos de la tesis que no aparezcan en el contexto entregado.

Devuelve EXCLUSIVAMENTE un objeto JSON con las claves:
{
  "eje":                       código del eje temático dado,
  "texto":                     la pregunta a pronunciar,
  "dificultad":                "basica" | "intermedia" | "profunda",
  "requiere_seguimiento":      true si la respuesta previa fue débil Y toca indagar antes de avanzar
}"""


def _preguntar(sesion, eje: dict, es_seguimiento: bool) -> dict:
    """Pregunta principal de un eje: LLM si está vivo, plantilla si no."""
    resumen_extraido = (sesion.resumen or "").strip()
    usuario = _construir_contexto(sesion, eje)

    dict_llm = llm.chat_json(
        _SISTEMA_AURA,
        usuario + "\n\nDevuelve el JSON con la pregunta del eje «" + eje["codigo"] + "».",
    )

    if dict_llm and dict_llm.get("texto"):
        pregunta = str(dict_llm["texto"]).strip()
        dificultad = str(dict_llm.get("dificultad", "intermedia"))
    else:
        pregunta = eje["plantilla"].format(tema_corto=_tema_corto(sesion.tema))
        dificultad = "intermedia"

    return {
        "tipo": "seguimiento" if es_seguimiento else "principal",
        "eje": eje["codigo"],
        "eje_etiqueta": eje["etiqueta"],
        "texto": pregunta,
        "dificultad": dificultad,
    }


def _pregunta_seguimiento(sesion, turno_previo, evaluacion: dict) -> dict:
    """Retro-pregunta de aterrizaje sobre el criterio más débil detectado."""
    criterios = evaluacion.get("criterios") or {}
    critico = min(
        criterios.items(),
        key=lambda kv: kv[1].get("puntaje", 0),
        default=(None, None),
    )[0]

    llave = CRIT_TO_SEGUIMIENTO.get(critico, "coherencia")
    usuario = (
        _construir_contexto(sesion, None)
        + f"\n\nLa respuesta previa del estudiante fue: «{turno_previo.respuesta}»\n"
        + f"El estudio detectó debilidad en el criterio {critico}: "
        + (evaluacion["criterios"][critico].get("justificacion", "") if critico else "")
        + "\nFormula una retro-pregunta pidiéndole aterrizar y respaldar esa respuesta "
          "(plantear la deficiencia de forma constructiva)."
    )
    dict_llm = llm.chat_json(_SISTEMA_AURA, usuario)

    if dict_llm and dict_llm.get("texto"):
        return {
            "tipo": "seguimiento",
            "eje": turno_previo.eje,
            "eje_etiqueta": turno_previo.eje_etiqueta,
            "texto": str(dict_llm["texto"]).strip(),
            "dificultad": "basica",
        }

    plantilla = RETRO_PLANTILLAS.get(llave, RETRO_PLANTILLAS["coherencia"])
    return {
        "tipo": "seguimiento",
        "eje": turno_previo.eje,
        "eje_etiqueta": turno_previo.eje_etiqueta,
        "texto": plantilla.format(tema_corto=_tema_corto(sesion.tema)),
        "dificultad": "basica",
    }


CRIT_TO_SEGUIMIENTO: dict[str, str] = {
    "pertinencia": "pertinencia",
    "coherencia": "coherencia",
    "fundamentacion": "fundamentacion",
    "metodologia": "metodologia",
}


def pensamiento_aleatorio() -> str:
    """Frase visible mientras AURA procesa (detalle de experiencia de uso)."""
    return random.choice(PENSAMIENTOS)


# ═══════════════════════════════════════════════════════════════════
#  Ayudantes
# ═══════════════════════════════════════════════════════════════════
def _tema_corto(tema: str) -> str:
    tema = (tema or "").strip()
    return tema if len(tema) <= 60 else tema[:57].rstrip() + "…"


def _construir_contexto(sesion, eje: dict | None) -> str:
    """Empaqueta el contexto de la tesis y del historial para el LLM."""
    fragmento = [f"TEMA DE GRADO: {sesion.tema}"]
    if sesion.resumen:
        fragmento.append(f"RESUMEN PROPORCIONADO:\n{sesion.resumen}")
    if sesion.enfoque:
        fragmento.append(f"ENFOQUE ACADÉMICO: {sesion.enfoque}")

    if sesion.turnos:
        fragmento.append("HISTORIAL RECENTE:")
        for turno in sesion.turnos[-3:]:
            fragmento.append(f"· EJE {turno.eje_etiqueta} — PREGUNTA: {turno.pregunta}")
            fragmento.append(f"  RESPUESTA: {turno.respuesta[:600]}")

    if eje:
        fragmento.append(
            f"TURNO ACTUAL — EJE «{eje['codigo']}» ({eje['etiqueta']}): "
            f"debes indagar sobre: {eje['enfoque']}"
        )
    return "\n\n".join(fragmento)
