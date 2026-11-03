# Arquitectura de Tutoia (MVP V1 · 2026)

> Documento técnico de la decisión de diseño. Complementa el capítulo de
> diseño/architectura de la tesis: aquí queda el *por qué* detrás del *cómo*.

## 1. Vista general

```
┌──────────────────────────── FRONTEND (React 18 + Vite) ────────────────────────────┐
│  Landing (/)                      Sala (/#/sala?s=<id>)                            │
│  · configuración de sesión        · <AvatarAURA/> SVG con 5 estados                │
│  · caso demo impactante           · Folio conversa + <PanelMetricas/> en vivo      │
│                                   · STT (mic) / TTS (voz de AURA) · velo de cierre │
└──────────────────────────────┬─────────────────────────────────────────────────────┘
                               │ fetch JSON (same-origin, sin CORS)
┌──────────────────────────────▼───────────── BACKEND (FastAPI · Python 3.12) ────────┐
│  /api/sesiones            → creación de sesión (OE 1)                               │
│  /api/sesiones/{id}/iniciar    → guion de apertura + 1.ª pregunta (OE 2)            │
│  /api/sesiones/{id}/responder  → análisis + turno adaptativo (OE 3)                 │
│  /api/sesiones/{id}/acta       → nota consolidada + acta HTML (OE 4)                │
│  /api/reportes/{acta}          → acta imprimible a PDF                              │
│                                                                                     │
│  dialog.py ──► ejes temáticos, retro-preguntas, guiones de AURA                      │
│  evaluator.py ► doble motor: heurístico local ⇄ LLM en la nube                       │
│  llm.py ─────► abstracción OpenAI-compatible (degradación elegante)                  │
│  report.py ──► acta SVG autocontenida (radar, historial, bandas)                     │
│  storage/ ───► sesiones JSON (persistencia y restauración al reiniciar)              │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Decisiones de diseño (y su justificación)

### 2.1 Doble motor de análisis («degradación elegante»)
Una sustentación es un evento académico **irrepetible**. Por ello el juicio
semántico (LLM en la nube) coexiste con un motor heurístico local
determinista que pondera señales medibles: cobertura léxica del resumen,
marcadores argumentativos, referentes teóricos, vocabulario metodológico y
marcadores de evasión. Si la red o la cuota fallan, la plataforma continúa
sin interrumpir el evento — y además el jurado puede **auditar** la
señal detrás de cada puntaje (principio de explicabilidad).

### 2.2 Diálogo adaptativo acotado por política
Los ejes replican la lógica causal de un tribunal: contexto → problema →
teoría → método → resultados → aportes. Cuando el análisis detecta un
criterio débil (< 2.5), AURA formula **una** retro-pregunta de aterrizaje
por eje (máximo 1, política institucional). Esto evita bucles de
repreguntas que desgasten al estudiante — decisión defendible en la
defensa del comité de ética y de metodología.

### 2.3 Voz nativa de navegador (Web Speech API)
El MVP elimina servidores de voz: TTS y STT corren en el cliente.
Ventajas: costo cero, latencia mínima, sin llaves. El trade-off (calidad
menor de transcripción) es aceptable para la demo y se resuelve en V2 con
Whisper local — la interfaz ya encapsula el proveedor en `lib/vozAula.js`,
o sea que el motor de voz es intercambiable.

### 2.4 Avatar en SVG puro
`AvatarAURA` es un componente React que implementa una máquina de estados
visual: `idle · escuchando · pensando · hablando · saludo`. El parpadeo es
autónomo (interval aleatorio 2.4–4.6 s) y la boca se anima vía
`requestAnimationFrame` mientras la síntesis de voz está activa. Sin
dependencias de render 3D: corre en cualquier portátil del jurado.

### 2.5 Persistencia continua
Cada turno se serializa a `storage/sesiones/<id>.json`; al arrancar, el
backend **restaura** las sesiones. Esto protege la demo ante un reinicio
accidental del servidor y deja trazabilidad auditable del evento.

## 3. Contratos de la API

| Método | Ruta | Propósito |
|---|---|---|
| POST | `/api/sesiones` | Crear sesión (estudiante, tema, resumen, nº de ejes) |
| POST | `/api/sesiones/{id}/iniciar` | Apertura de AURA + primera pregunta (idempotente) |
| POST | `/api/sesiones/{id}/responder` | Análisis de respuesta + siguiente turno |
| POST | `/api/sesiones/{id}/acta` | Nota consolidada + acta autocontenida |
| GET  | `/api/reportes/{archivo}` | Descarga/impresión del acta |
| GET  | `/api/rubrica` | Rúbrica institucional integrada |
| GET  | `/api/health` | Latido + motor activo |

## 4. Calibración del motor heurístico

La fórmula del puntaje fue calibrada en el desarrollo con cuatro arquetipos
de respuesta: **FUERTE → 4.3 (Sobresaliente)**, **MEDIA → 1.5–2.5
(Insuficiente/Aceptable)**, **VAGA → 0.9 (Crítico)**, **EVASIVA → 0.0**
(mismo eje, señal explícita de «no sé»). El «piso argumental» (respuestas
≥ 25 palabras) evita penalizar ideas válidas expresadas con vocabulario
simple. En `live` la calificación jerárquica la produce el LLM con la
misma rúbrica, de modo que ambos motores comparten la escala 0–5.

## 5. Escalado a V2

Los puntos de extensión ya están definidos por la arquitectura:
- **STT/TTS**: reemplazar `vozAula.js` por Whisper local (misma interfaz).
- **LLM**: `llm.py` es OpenAI-compatible: se puede apuntar a cualquier proveedor u Ollama sin tocar dominio.
- **Rúbrica**: `evaluator.py` carga criterios/ponderaciones; versionar en JSON sobre `data/`.
- **Persistencia**: sustituir los volcados JSON por SQLite/PostgreSQL sin revisar el dominio.
- **Avatar**: la máquina de estados es la interfaz; un render WebGL se enchufa sobre la misma lógica.
