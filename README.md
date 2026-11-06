# TUTOIA 2026

**Plataforma inteligente con avatar evaluador para la automatización de sustentaciones de trabajos de grado mediante procesamiento de lenguaje natural** · Unidades Tecnológicas de Santander · Periodo 2026.

## 🔍 ¿De qué trata el proyecto?

Tutoia es un sistema web que apoya el proceso de **evaluación sumativa** de las sustentaciones de trabajo de grado. En la sustentación, **AURA** (Avatar Universitario para la Retroalimentación Académica), el avatar evaluador de la plataforma, reproduce el papel de un tribunal virtual:

1. **Conduce la sesión** — presenta el guion, da la bienvenida al sustentante y formula preguntas organizadas en **6 ejes temáticos** que replican la lógica de un jurado real: contextualización · problema y alcance · marco teórico · metodología · resultados · conclusiones.
2. **Escucha y analiza en tiempo real** — el estudiante responde hablando (dictado por voz) o escribiendo; el motor de **procesamiento de lenguaje natural** evalúa cada respuesta contra la **rúbrica institucional** con 4 criterios ponderados (escala 0–5): pertinencia (30 %), coherencia (25 %), fundamentación teórica (25 %) y dominio metodológico (20 %).
3. **Indaga de forma adaptativa** — si una respuesta se detecta débil en algún criterio, AURA formula una retro-pregunta de refuerzo antes de avanzar de eje (máximo una por eje, como política institucional).
4. **Emite el acta de evaluación** — al terminar, la plataforma genera automáticamente un **acta** con la nota consolidada, el radar de criterios, la línea de tiempo del desempeño (pregunta por pregunta), fortalezas, oportunidades y bandas cualitativas, lista para imprimir o guardar en PDF como insumo del jurado humano.

El análisis semántico se apoya en un **doble motor**: un **LLM en la nube** (juicio semántico completo) y un **motor heurístico local** (señales léxicas medibles que garantizan que la sustentación nunca se interrumpa ante un fallo de red — importante porque es un evento académico irrepetible).

**Tecnologías:** Python 3.12 · FastAPI · React 18 + Vite · SVG animado para el avatar · Web Speech API (voz nativa del navegador, cero costo).

---

## 🚀 Guía de ejecución detallada

### Requisitos previos

| Software | Versión mínima | Verificar con |
|---|---|---|
| Python | 3.12 | `python3 --version` |
| Node.js | 18 | `node --version` |
| npm | 9 | `npm --version` |
| Navegador | Chrome o Edge (necesario para la voz) | — |

> **Nota sobre Python en Ubuntu/Debian:** si el sistema tiene Python gestionado por apt (PEP 668), el entorno virtual se crea sin `pip`; la guía incluye el paso para instalarlo dentro del venv (paso 3).

---

### Paso 1 — Obtener el proyecto

```bash
cd ~/Documentos        # o la carpeta donde lo tengas
cd TUTOIA              # raíz del repositorio
```

---

### Paso 2 — Crear el entorno virtual del backend

```bash
cd backend                            # la consola queda en backend/
python3 -m venv --without-pip .venv   # crea el entorno sin pip
.venv/bin/python /tmp/get-pip.py -q   # instala pip dentro del venv*
.venv/bin/pip install -U pip -q
```

\* Si no existe `/tmp/get-pip.py`, descárgalo primero:

```bash
python3 -c "import urllib.request; urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', '/tmp/get-pip.py')"
```

**En equipos donde `python3 -m venv` funciona normal**, basta con:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

---

### Paso 3 — Instalar dependencias del backend

```bash
.venv/bin/pip install -r requirements.txt
```

Esto instala: `fastapi`, `uvicorn[standard]` (servidor web), `python-dotenv` (variables de entorno) y `openai` (cliente compatible con cualquier proveedor de LLM).

---

### Paso 4 — Configurar el motor de IA

Copia la plantilla de configuración y elige el modo:

```bash
cp .env.example .env
```

Edita `backend/.env`. Hay **dos modos**:

#### Opción A · Modo `mock` (recomendado para empezar y para la demo)

```env
LLM_MODE=mock
```

- ✅ No requiere internet, clave de API ni cuenta.
- ✅ Toda la evaluación la realiza el motor heurístico local.
- ✅ Es el modo a prueba de fallos para presentar ante el jurado.
- 📌 Es el valor por defecto: si no lo cambias, todo funciona sin más.

#### Opción B · Modo `live` (análisis semántico con LLM en la nube)

```env
LLM_MODE=live
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

- La plataforma es **compatible con OpenAI, DeepSeek, Groq, Together y OpenRouter**: solo cambia `LLM_BASE_URL` y `LLM_MODEL`.
- Si el proveedor o la falla de la red en plena sesión, el motor heurístico local toma el turno automáticamente (degradación elegante).

---

### Paso 5 — Instalar dependencias del frontend (React + Vite)

Desde la raíz del repositorio:

```bash
cd ../frontend        # o `cd frontend` desde la raíz
npm install
```

Esto instala React 18, ReactDOM y Vite 5 (aprox. 63 paquetes, toma menos de 1 minuto).

---

### Paso 6 — Compilar el frontend

```bash
npm run build
```

Genera la carpeta `frontend/dist/` con el build de producción de React que FastAPI servirá estáticamente. Verás algo como:

```
dist/index.html                  0.96 kB
dist/assets/index-*.css         18 kB
dist/assets/index-*.js         165 kB
✓ built in ~2s
```

> Para hacer cambios en el frontend durante el desarrollo, usa `npm run dev` (levanta Vite en `http://localhost:5173` con recarga en caliente y redirige `/api` al backend en el 8000). Para la demo, siempre compila con `npm run build`.

---

### Paso 7 — Levantar la plataforma (backend + frontend juntos)

```bash
cd ../backend
.venv/bin/uvicorn app.main:app --port 8000
```

Salida esperada:

```
INFO:     Started server process [...]
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Con el servidor encendido, el frontend compilado ya se sirve desde la misma dirección: **un solo comando enciende todo el sistema**.

Verifica que viva (en otra terminal o desde el navegador):

```bash
curl http://localhost:8000/api/health
{"servicio":"Tutoia","version":"0.1.0","motor":"heuristico-local", ...}
```

---

### Paso 8 — Usar la plataforma (flujo de la demo)

1. **Abre la plataforma** → <http://localhost:8000> (navegador Chrome o Edge).
2. **⚡ Cargar caso demo** → el formulario se llena con una tesis de ejemplo lista para la presentación.
3. Presiona **🛰️ Abrir sala de sustentación** → entra a la sala en vivo: AURA da su bienvenida y pronuncia la primera pregunta (con voz del navegador; si el audio no se escucha usa el botón 🔇/🔊 de la barra superior o **⏭ Saltar voz**).
4. **Responde por voz** → botón 🎙️ (permite el micrófono cuando el navegador lo pida), habla con calma y pulsa el micrófono para detener la escucha; tu dictado queda en el campo de texto (puedes ajustarlo antes de enviar). También puedes escribir la respuesta directamente.
5. Pulsa **Aceptar ➤** → AURA entra en modo *Analizando* y el panel superior muestra en vivo la nota acumulada, las barras por criterio y el avance de ejes; luego pronuncia la siguiente pregunta (o un refuerzo, si la respuesta se detectó débil).
6. Repite hasta completar los 6 ejes (los refuerzos aparecen etiquetados como *refuerzo* en el folio de conversación).
7. Al finalizar el último eje, AURA consolida la evaluación: aparece la **nota final sobre 5.0** con su banda cualitativa y el botón **📊 Abrir acta**.
8. El acta se abre en una pestaña nueva: pulsa **⎙ Imprimir / Guardar PDF** para exportarla tal cual la entregará al jurado.

**Alternativa para pruebas rápidas por consola (sin navegador):**

```bash
# crear sesión
curl -s -X POST http://localhost:8000/api/sesiones \
  -H "Content-Type: application/json" \
  -d '{"estudiante":"Nombre del Estudiante","enfoque":"Ingeniería de Sistemas","tema":"Tema del trabajo de grado","resumen":"Resumen con problema, metodología, resultados y conclusiones del trabajo (mínimo 40 caracteres).","total_preguntas":6}'

# inicia y devuelve la apertura + primera pregunta
curl -s -X POST http://localhost:8000/api/sesiones/<ID>/iniciar

# responder (repetir hasta que la respuesta contenga "cierre": true)
curl -s -X POST http://localhost:8000/api/sesiones/<ID>/responder \
  -H "Content-Type: application/json" \
  -d '{"texto":"Respuesta del estudiante de al menos 4 palabras."}'

# generar acta
curl -s -X POST http://localhost:8000/api/sesiones/<ID>/acta
```

---

### Paso 9 — Apagar y reiniciar

- **Apagar:** `CTRL + C` en la terminal del servidor. Si aún tienes el venv activo, cierra sesión con `deactivate` (opcional).
- **Reiniciar:** repite solo el Paso 7 — el backend **restaura automáticamente** las sesiones anteriores (historial, notas y actas) gracias a la persistencia en `backend/app/storage/`.
- Si cambias `.env` (modo mock → live), reinicia el servidor para que aplique.

---

### 🛠️ Solución de problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `python3 -m venv` falla ("ensurepip") | Python gestionado por apt (PEP 668) | Usa la variante `--without-pip` + get-pip del Paso 2 |
| `Cannot import name 'dialog'` o similar al iniciar | Servicio corrido desde la carpeta equivocada | Uvicorn requiere ejecutarse **dentro de `backend/`**: `cd backend && .venv/bin/uvicorn app.main:app --port 8000` |
| La sala queda "Acondicionando…" | El navegador cargó una sesión vieja | Recarga la página (F5); las sesiones se restauran del storage |
| Al abrir sala aparece "⚠ La sesión no existe" | Se reinició el servidor o cambió el ID | Vuelve a la landing y crea la sesión de nuevo |
| No se escucha la voz de AURA | Navegador sin voz en español | Chrome/Edge con paquete de voz es; usa **⏭ Saltar voz** para continuar |
| Al abrir sala aparece "⚠ El navegador no soporta reconocimiento de voz" | Firefox u otro sin Web Speech STT | Usa Chrome o Edge |
| El micrófono no activa la escucha | Permiso denegado | Ícono de candado en la barra de direcciones → Permitir micrófono → recarga |
| `422 La respuesta es demasiado corta` | Menos de 4 palabras | Escribe/conserva una respuesta con más contenido |
| Acta no se encuentra (`404`) | El archivo fue borrado | Genera el acta de nuevo: `POST /api/sesiones/<ID>/acta` |
| Puerto 8000 ocupado | Otro proceso usando el puerto | `fuser -k 8000/tcp` (Linux) y levanta de nuevo |

---

### 📁 Estructura del proyecto (referencia rápida)

```
TUTOIA/
├── backend/
│   ├── .env                     ← tu configuración (no se sube al repo)
│   ├── .env.example             ← plantilla de configuración
│   ├── requirements.txt         ← dependencias de Python
│   └── app/
│       ├── main.py              ← API FastAPI: sesiones, turnos, acta
│       ├── config.py            ← configuración del sistema
│       ├── data/rubrica_uts.json
│       ├── services/
│       │   ├── dialog.py        ← guion adaptativo de AURA (6 ejes + refuerzos)
│       │   ├── evaluator.py     ← motor doble de evaluación (rúbrica 0–5)
│       │   ├── llm.py           ← capa del LLM en la nube (degradación elegante)
│       │   └── report.py        ← generador del acta (HTML + SVG)
│       └── storage/             ← sesiones JSON y actas (runtime)
├── frontend/                    ← React 18 + Vite
│   ├── src/components/
│   │   ├── AvatarAURA.jsx       ← avatar SVG con 5 estados animados
│   │   ├── Landing.jsx          ← presentación + configuración de sesión
│   │   ├── Sala.jsx             ← sala de sustentación en vivo
│   │   ├── PanelMetricas.jsx    ← análisis en tiempo real
│   │   └── FolioConversa.jsx    ← folio de la sustentación
│   └── dist/                    ← build de producción (servido por el backend)
└── docs/arquitectura.md         ← decisiones de diseño (para la tesis)
```

---

*Proyecto de grado · Unidades Tecnológicas de Santander · 2026.*
