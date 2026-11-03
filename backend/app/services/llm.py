"""
Tutoia · Capa de abstracción del modelo de lenguaje.

La plataforma opera bajo una estrategia de **degradación elegante**:
el juicio semántico profundo es responsabilidad del LLM en la nube, pero
la plataforma NUNCA queda inoperante: si no hay red, cuota o clave, el
motor heurístico local (``evaluator.py`` / ``dialog.py``) toma el control
de forma transparente. Este diseño garantiza que la sustentación —un
evento académico irrepetible— sea a prueba de fallos de infraestructura.
"""
import json
import logging
import re

from openai import OpenAI

from app.config import settings

logger = logging.getLogger("tutoia.llm")


def motor_activo() -> str:
    """Nombre descriptivo del motor que se usará en el siguiente turno."""
    if settings.LLM_MODE == "live" and settings.LLM_API_KEY:
        return f"llm-nube:{settings.LLM_MODEL}"
    return "heuristico-local"


def hay_llm_disponible() -> bool:
    """True si el modo live está configurado y la clave está presente."""
    return settings.LLM_MODE == "live" and bool(settings.LLM_API_KEY)


def chat_json(system: str, user: str, temperatura: float | None = None) -> dict | None:
    """
    Solicita al LLM una respuesta **estrictamente en JSON**.

    Devuelve ``None`` cuando el motor local debe asumir el turno (modo mock
    o error del proveedor). Los llamadores implementan siempre un respaldo
    determinista, así que ``None`` jamás detiene la plataforma.
    """
    if not hay_llm_disponible():
        return None

    try:
        cliente = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            timeout=30.0,
        )
        respuesta = cliente.chat.completions.create(
            model=settings.LLM_MODEL,
            temperature=temperatura if temperatura is not None else settings.LLM_TEMPERATURE,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        texto = respuesta.choices[0].message.content or ""
        return _extraer_json(texto)
    except Exception as exc:  # noqa: BLE001 — la resiliencia es un requisito del producto
        logger.warning("LLM en la nube no disponible (%s); asume el motor heurístico.", exc)
        return None


def _extraer_json(texto: str) -> dict | None:
    """Parsea JSON tolerando preámbulos conversacionales del modelo."""
    texto = texto.strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass
    # Rescate: primer bloque {...} balanceado dentro del texto libre.
    coincidencia = re.search(r"\{[\s\S]*\}", texto)
    if coincidencia:
        try:
            return json.loads(coincidencia.group(0))
        except json.JSONDecodeError:
            return None
    return None
