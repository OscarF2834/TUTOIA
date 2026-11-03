# ══════════════════════════════════════════════════════════════════
#  TUTOIA 2026 · Plataforma inteligente con avatar evaluador
# ══════════════════════════════════════════════════════════════════

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)

**Tutoia** es una plataforma inteligente con avatar evaluador — **AURA**
(Avatar Universitario para la Retroalimentación Académica) — para la
automatización de sustentaciones de trabajos de grado mediante
**procesamiento de lenguaje natural**. Unidades Tecnológicas de Santander · Periodo 2026.

```
     Estudiante sustenta ⇄ AURA pregunta, escucha y evalúa en vivo
                                    │
        Motor PLN ──────────────────┤ # rúbrica institucional (0–5)
   (LLM en la nube + respaldo       │ # pertinencia · coherencia
    heurístico local)               │ # fundamentación · metodología
                                    ▼
                 Acta de evaluación (radar, línea de tiempo, bandas)
```

## ⚡ Arranque rápido (5 comandos)

```bash
# 1. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Motor de IA (elige uno)
cp .env.example .env       # LLM_MODE=mock  →  funciona SIN internet ni clave
# ...o edita .env con LLM_MODE=live + LLM_API_KEY=<tu clave>

# 3. Frontend (React + Vite)
cd ../frontend
npm install && npm run build

# 4. Encender todo
cd ../backend
uvicorn app.main:app --port 8000
```

Abre **http://localhost:8000** · presiona **⚡ Cargar caso demo** ·
**Abre la sala de sustentación** · responde con voz (micrófono) o texto ·
finaliza y abre el **acta automática** (⎙ Imprimir → PDF).

> 💡 **Modo demo a prueba de fallos:** con `LLM_MODE=mock` la plataforma opera
> 100 % local — ideal para la exposición ante el jurado sin riesgo de caída
> de red. Con `LLM_MODE=live` el análisis semántico lo realiza un LLM en la nube
> (compatible con OpenAI, DeepSeek, Groq, OpenRouter, etc.).

## 🧩 Arquitectura del MVP

| Componente | Tecnología | Rol |
|---|---|---|
| Orquestador | **FastAPI** (Python 3.12) | Ciclo de sesión, guion adaptativo, acta |
| Motor de diálogo | `services/dialog.py` | 6 ejes temáticos + retro-preguntas adaptativas |
| Motor evaluador | `services/evaluator.py` | **Doble motor**: LLM en nube + heurística local trazable |
| Capa LLM | `services/llm.py` | Abstracción OpenAI-compatible con degradación elegante |
| Acta | `services/report.py` | HTML autocontenida con radar y barras en SVG nativo |
| Frontend | **React 18 + Vite** | Landing, sala de sustentación, panel métricas en vivo |
| Avatar AURA | SVG + rAF (componente `AvatarAURA`) | 5 estados animados, parpadeo, boca sincronizada a TTS |
| Voz | Web Speech API (`lib/vozAula.js`) | STT es-CO/TTS nativo del navegador: cero costo |

**Decisionos de ingeniería presentables ante el jurado:**

1. **Doble motor de evaluación** — el LLM produce el juicio semántico y el
   motor heurístico local garantiza que la sustentación (un evento
   irrepetible) nunca dependa de la red; sus señales léxicas
   (cobertura, conectores, referentes) quedan como evidencia trazable.
2. **Diálogo adaptativo con política institucional** — máximo 1 refuerzo
   por eje temático: AURA profundiza una sola vez y avanza; la debilidad
   se refleja en el acta, no en el agotamiento del estudiante.
3. **Degradación elegante** — sin clave ni internet, el sistema continúa
   con calidad determinista (`mock`).
4. **Persistencia continua** — cada turno se volca a JSON y se restaura al
   reiniciar el servidor: la prueba del sistema no pierde su historial.
5. **Voz nativa del navegador** — Web Speech API elimina costo,
   latencia y dependencias de nube para el MVP (evolución: Whisper local).

## 🎯 Correspondencia con los objetivos específicos

| Objetivo específico | Implementación en el MVP |
|---|---|
| **1.** Requerimientos y rúbricas | `evaluator.py` + `data/rubrica_uts.json` (4 criterios ponderados, bandas cualitativas, ejes temáticos) |
| **2.** Arquitectura del software y flujo de diálogo | `dialog.py` (ejes progresivos, indagación adaptativa) + `docs/arquitectura.md` |
| **3.** Plataforma web con PLN + avatar interactivo | `main.py` (API) + React `Landing`/`Sala` + AURA animado con STT/TTS |
| **4.** Validación técnica y desempeño evaluativo | Acta automatizada (nota ponderada, radar, línea de tiempo) como insumo del análisis comparativo jurado humano vs. plataforma |

## 🗺️ Ruta de evolución (post-MVP)

- [ ] **V2** — Whisper local para STT robusto + memoria semántica de la tesis (embeddings del documento completo)
- [ ] **V2** — Registro del acta en base de datos (SQLite → PostgreSQL) y firma del jurado
- [ ] **V2** — Panel del jurado comparativo (corrector vs. plataforma) para el objetivo 4
- [ ] **V3** — Fine-tuning/evaluación automatizada con corpus real de sustentaciones UTS
- [ ] **V3** — AURA en estilo 3D (WebGL) conservando la misma máquina de estados

## 📚 Referencias que sustentan el enfoque

- Martínez-Comesaña et al. (2023) — rúbricas y evaluación de las competencias comunicativas en ingeniería.
- Arias-Chávez et al. (2024) · Artiles-Rodríguez et al. (2021) — inteligencia artificial aplicada a la evaluación formativa/sumativa en educación superior.

---

*Proyecto de grado · Unidades Tecnológicas de Santander · 2026 —
Desarrollo: equipo TUTOIA (Oscar & compañero de proyecto).*
