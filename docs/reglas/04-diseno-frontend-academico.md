# 04 · Diseño Frontend Académico Institucional (Academic SaaS)

> **Alcance:** Sistema de diseño visual, paleta de colores Tailwind CSS, tipografía, accesibilidad, modales seguros y patrones UX para carga de archivos FDC y retroalimentación evaluativa en TutoIA.

---

## 1. Filosofía Visual: «Academic SaaS Institucional»

TutoIA es una herramienta formal de evaluación universitaria para las **Unidades Tecnológicas de Santander (UTS)** utilizada por estudiantes en momento de sustentación y por docentes jurados. Por tanto, su interfaz debe transmitir **seriedad académica, claridad documental, calma cognitiva y transparencia algorítmica** (`RNF-06`, `RNF-07`, `RNF-10`).

### 1.1 Estética obligatoria vs. estética prohibida

| Obligatorio (Academic SaaS Luminoso) | Terminantemente Prohibido |
| :--- | :--- |
| Modo claro institucional con lienzos `bg-slate-50` y `bg-slate-100`. | Fondos oscuros tipo *cyberpunk*, espaciales o *gaming* (`bg-black`, morados/azules nocturnos). |
| Superficies de lectura blancas puras (`bg-white`) con bordes finos `border-slate-200` y sombras sutiles (`shadow-sm`). | Efectos *glassmorphism* borrosos sobre textos extensos, bordes neón o sombras fluorescentes (`drop-shadow` brillante). |
| Acento institucional sobrio (verde académico UTS `emerald-700`/`emerald-600` y azul informativo `blue-700`/`sky-700`). | Gradientes arcoíris, cian/magenta eléctrico o animaciones decorativas que distraigan al sustentante. |
| Iconografía limpia de trazo uniforme (SVG monocromático `stroke-width="1.75"` o `2`) en lugar de exceso de emojis informales. | Saturar botones y encabezados formales con emojis infantiles o jerga coloquial. |

---

## 2. Sistema de Tokens Visuales en Tailwind CSS

### 2.1 Superficies y Bordes
- **Fondo global de la aplicación:** `bg-slate-50 text-slate-900 antialiased`
- **Paneles secundarios / cabeceras de tabla / zonas de código o metadatos:** `bg-slate-100/80`
- **Tarjetas y contenedores principales (`Card`):** `bg-white border border-slate-200 rounded-xl shadow-sm`
- **Divisores internos:** `border-slate-200` o `divide-slate-200`

### 2.2 Jerarquía Tipográfica y Numérica
- **Familia tipográfica:** `Inter` (o `Plus Jakarta Sans` / pila `system-ui` limpia), garantizando lectura fluida de párrafos extensos de tesis y transcripciones.
- **Títulos principales:** `text-slate-900 font-semibold tracking-tight` (evitar pesos extremos `font-black` con sombras).
- **Cuerpo de lectura académica (resúmenes FDC, preguntas de AURA, transcripción):** `text-slate-700 leading-relaxed text-sm md:text-base`.
- **Etiquetas y metadatos secundarios:** `text-slate-500 text-xs font-medium`.
- **Calificaciones, pesos de rúbrica y cronómetros:** aplicar siempre `tabular-nums` para alineación vertical exacta de cifras (`4.25 / 5.0`, `30 %`, `08.4 s`).

### 2.3 Paleta Semántica Institucional y de Conceptos UTS

| Rol semántico | Texto / Icono | Fondo suave | Borde | Uso exacto en TutoIA |
| :--- | :--- | :--- | :--- | :--- |
| **Acento Primario Institucional (UTS)** | `text-white` (en botón sólido) / `text-emerald-800` (en chip) | `bg-emerald-700` (hover `bg-emerald-800`) / `bg-emerald-50` | `border-emerald-200` | Acciones primarias («Analizar F-DC-125», «Iniciar sustentación»), identidad UTS y progreso activo. |
| **Acento Secundario Académico** | `text-sky-800` / `text-blue-700` | `bg-sky-50` | `border-sky-200` | Notas metodológicas, enlaces a secciones del documento FDC, estado informativo del motor Gemini. |
| **Concepto `APROBADO` (`≥ 3.0`)** | `text-emerald-800` | `bg-emerald-50` | `border-emerald-300` | Veredicto aprobatorio, criterios con desempeño alto (`≥ 3.5`) y validaciones exitosas del FDC. |
| **Concepto `APLAZADO` (`> 1.0 y < 3.0`)** | `text-amber-800` | `bg-amber-50` | `border-amber-300` | Veredicto aplazado, advertencias de coherencia parcial en el FDC y repreguntas de refuerzo. |
| **Concepto `NO APROBADO` (`≤ 1.0`) / Error** | `text-rose-800` | `bg-rose-50` | `border-rose-300` | Caso excepcional crítico (`0.0 – 1.0`), desalineación grave en el FDC o error de validación de archivo. |

---

## 3. Accesibilidad, Responsividad y Modales a Prueba de Recorte

1. **Contraste WCAG 2.1 Nivel AA obligatorio (`RNF-07`):**
   - Ningún texto informativo puede tener relación de contraste `< 4.5:1` contra su fondo. Prohibido usar `text-slate-300` o `text-slate-400` para textos legibles sobre fondo blanco (usar mínimo `text-slate-500` o `text-slate-600`).
2. **Modales blindados contra recorte de pantalla (`max-h-[90vh]`):**
   - Muchos equipos en salas universitarias operan a `1366×768` o con escalado al `125 %`.
   - Todo componente `Modal` debe estructurarse como `max-h-[90vh] w-full flex flex-col overflow-hidden`:
     - **Cabecera (`header`):** fija (`shrink-0 border-b border-slate-200 px-6 py-4`).
     - **Cuerpo (`body`):** único contenedor con desplazamiento vertical (`flex-1 overflow-y-auto px-6 py-4`).
     - **Pie de acciones (`footer`):** siempre visible (`shrink-0 border-t border-slate-200 bg-slate-50 px-6 py-4`).
3. **Navegación por teclado y lectores de pantalla:**
   - Todos los controles interactivos incluyen `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2`.
   - Los cambios dinámicos de estado (progreso de análisis del FDC, activación de micrófono, turno de AURA) notifican mediante regiones `aria-live="polite"`.
4. **Diseño imprimible para Actas (`@media print`):**
   - La vista de acta y escrito completo debe ocultar barras de navegación y botones al imprimir, forzando fondo blanco puro, bordes definidos y gráficos SVG legibles tanto en color como en escala de grises.

---

## 4. Estados Visuales Obligatorios para Flujos Críticos

### 4.1 Carga de Archivos FDC (`FileDropzone`)
Nunca mostrar un `<input type="file">` nativo suelto. El área de carga debe comunicar inequívocamente **5 estados**:
1. **Reposo (`idle`):** Borde punteado `border-2 border-dashed border-slate-300 bg-slate-50/60 hover:border-emerald-500 hover:bg-emerald-50/30`, indicando claramente formatos admitidos (`PDF` o `DOCX`), formato seleccionado (`F-DC-124` o `F-DC-125`) y peso máximo (`20 MB`).
2. **Arrastre activo (`dragging`):** Realce `border-emerald-600 bg-emerald-50/60` confirmando que puede soltar el documento.
3. **Archivo seleccionado / validado:** Tarjeta compacta con icono documental, nombre truncado con `title` completo, peso formateado (`2.4 MB`), insignia del formato y botón secundario «Cambiar archivo».
4. **Error de validación:** Contenedor `border-rose-300 bg-rose-50/60` con mensaje accionable en español formal (ej. *«Formato no admitido (.zip). Cargue el documento institucional en formato PDF o DOCX.»*) sin borrar los demás campos del formulario.
5. **Opción de Caso Demo Institucional (`RF-03`):** Acción secundaria claramente etiquetada («Cargar F-DC-125 de demostración») que precarga un análisis verificable para sustentaciones ante el comité sin requerir archivo local.

### 4.2 Barra de Progreso por Etapas para el Análisis FDC (`RNF-01`)
Dado que la ingesta y análisis estructurado con Google Gemini puede tardar entre `3` y `15` segundos, está **prohibido bloquear la pantalla con un spinner genérico sin contexto**. Se debe mostrar un indicador de progreso por etapas académicas comprensibles:
- **Paso 1:** Verificando integridad y estructura del formato FDC.
- **Paso 2:** Indexando documento en motor multimodal seguro.
- **Paso 3:** Extrayendo objetivos, metodología, coherencia y vacíos de sustentación.
- **Paso 4:** Síntesis lista — presentando radiografía académica del proyecto antes de ingresar a la sala.

### 4.3 Feedback de Evaluación y Transparencia *Human-in-the-Loop* (`RNF-10`, `RNF-11`)
- **Resumen previo a la sustentación (Módulo 1):** Al concluir el análisis del FDC, presentar en tarjetas limpias: metadatos extraídos (título, autores, modalidad), síntesis de problema/objetivos/metodología, semáforo de **hallazgos de coherencia** (*Alineado / Parcial / Desalineado*) y conteo de **focos de indagación detectados** que guiarán a AURA.
- **Desglose de evaluación por turno y final:** Mostrar barras horizontales limpias con valor numérico `0.0–5.0` y peso porcentual para los 4 criterios institucionales (*Pertinencia 30 %*, *Coherencia 25 %*, *Fundamentación 25 %*, *Metodología 20 %*), acompañadas de listas separadas de **Fortalezas** y **Oportunidades de mejora**.
- **Aviso ético obligatorio (*Human-in-the-Loop*):** Tanto el panel de resultados como el acta deben incluir un bloque informativo sobrio (`bg-slate-100 border border-slate-200 text-slate-600 text-xs`) indicando explícitamente que la evaluación generada por AURA es un **insumo técnico de apoyo** y que la calificación definitiva corresponde al jurado docente designado por las UTS.
