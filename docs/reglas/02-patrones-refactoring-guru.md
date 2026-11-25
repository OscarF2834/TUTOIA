# 02 · Catálogo Obligatorio de Patrones de Diseño (Refactoring.Guru)

> **Referencia canónica:** [Catálogo de Patrones de Diseño — Refactoring.Guru](https://refactoring.guru/design-patterns/catalog)  
> **Regla fundamental:** En TutoIA no se escriben patrones decorativos ni académicos de relleno; cada patrón aquí listado gobierna un punto real de variación o desacople del sistema.

---

## 1. Regla Explícita contra `if/else` y `switch` Crecientes

> **MANDATO OBLIGATORIO:** Antes de agregar un segundo `elif`, un `switch` por código de formato, una bandera booleana de control de flujo (`es_fdc_125`, `hubo_refuerzo_2`, `usar_fallback`) o un bloque `try/except` de infraestructura dentro de un caso de uso, **debes integrar esa lógica dentro del patrón asignado en este documento.**

| Si estás a punto de escribir... | Debes usar obligatoriamente... |
| :--- | :--- |
| Secuencia de `if` validando extensión, peso, hash, legibilidad y subida del archivo FDC | **Chain of Responsibility** |
| `if fdc_type == "FDC_124": ... elif fdc_type == "FDC_125": ...` o `if perfil_jurado == ...` | **Strategy** + **Factory Method** |
| `if sesion.estado == "en_curso" and not finalizada and pregunta_pendiente:` | **State** |
| Llamadas directas a `genai.Client()`, `pypdf`, `docx` o servicios STT/TTS en casos de uso | **Adapter** (detrás de un `Port` en `domain/ports/`) |
| Routers o componentes React coordinando 4–5 servicios/endpoints manualmente o usando `fetch` | **Facade** (`SustentacionFacade` / `FdcIngestionFacade` / `TutoiaApiFacade`) |
| Concatenación desordenada de HTML/SVG/JSON para armar el acta y escrito de sesión | **Builder** (`report_builder.py`) |
| Llamadas mezcladas de logs de auditoría, métricas de latencia y trazas dentro del evaluador | **Observer** (`DomainEventBus`) |

---

## 2. Inventario Oficial de Patrones Acoplados a TutoIA

### 2.1 Chain of Responsibility *(Comportamiento)*
- **Referencia:** `refactoring.guru/design-patterns/chain-of-responsibility`
- **Problema real en TutoIA:** La ingesta de un documento FDC requiere validaciones progresivas desde las más baratas en CPU/memoria hasta las más costosas en red/tokens (subida a Gemini Files API). Un archivo corrupto, vacío o que no corresponde a un formato académico no debe consumir cuota de Google Gemini ni abrir registros huérfanos.
- **Ubicación:** `backend/app/application/pipelines/fdc_ingestion/`
- **Estructura obligatoria:**
  - `IngestionHandler` (clase base abstracta con `set_next(handler)` y `handle(context: FdcIngestionContext)`).
  - Eslabones concretos en orden:
    1. `FileMetadataValidationHandler`: valida extensión (`.pdf`, `.docx`), *magic bytes* reales del binario, tamaño máximo permitido (ej. `≤ 20 MB`) y sanitiza el nombre de archivo (`RNF-12`).
    2. `FileDeduplicationHandler`: calcula hash `SHA-256` y verifica si el binario exacto ya posee un URI vigente en Gemini Files API.
    3. `FdcStructureValidationHandler`: inspecciona vía adaptador documental que el archivo no esté cifrado, contenga texto seleccionable suficiente y presente estructura académica mínima reconocible de un documento FDC de las UTS.
    4. `LocalStoragePersistenceHandler`: asegura respaldo privado del documento bajo identificador UUID seguro.
    5. `GeminiFilesUploadHandler`: sube el documento a Gemini Files API a través de `AiDocumentStoragePort` y registra `gemini_file_name`, `gemini_file_uri` y `expires_at` (TTL de 48 h) en el contexto.

---

### 2.2 Strategy *(Comportamiento)*
- **Referencia:** `refactoring.guru/design-patterns/strategy`
- **Problema real en TutoIA:** No se analiza ni se evalúa igual una **Propuesta de Grado (`F-DC-124`)** —donde aún no existen resultados ejecutados y prima la coherencia entre problema, justificación, objetivos y diseño metodológico propuesto— que un **Informe Final (`F-DC-125`)** —donde es obligatorio contrastar objetivos específicos contra resultados verificables, productos y conclusiones—. Del mismo modo, la evaluación de respuestas cambia según el perfil del jurado y el motor disponible (semántico en nube vs. heurístico local de contingencia `RNF-04`).
- **Ubicación:** Contratos en `backend/app/domain/strategies/`; implementaciones puras en `domain/strategies/` y estrategias asistidas por IA en `application/` + `infrastructure/ai/`.
- **Familias de estrategias obligatorias:**
  1. **`FdcAnalysisStrategy`**:
     - `Fdc124ProposalStrategy`: directrices de extracción, reglas de coherencia prospectiva y detección de vacíos de formulación/factibilidad.
     - `Fdc125FinalReportStrategy`: directrices de extracción completa, verificación de trazabilidad *Objetivos ↔ Metodología ↔ Resultados ↔ Conclusiones* y semillas de preguntas de defensa final.
  2. **`TurnEvaluationStrategy` y `JuryProfileStrategy`**:
     - Perfiles de énfasis evaluativo (p. ej. `BalancedUtsJuryStrategy`, `MethodologicalRigorStrategy`, `TheoreticalDepthStrategy`) aplicando la rúbrica institucional ponderada (Pertinencia 30 %, Coherencia 25 %, Fundamentación 25 %, Metodología 20 %).
     - Estrategia resiliente con degradación controlada: `GeminiSemanticEvaluationStrategy` (principal) y `HeuristicLexicalEvaluationStrategy` (respaldo determinista ante fallo de red o cuota).

---

### 2.3 State *(Comportamiento)*
- **Referencia:** `refactoring.guru/design-patterns/state`
- **Problema real en TutoIA:** Una sesión de sustentación atraviesa fases estrictas con operaciones permitidas e inválidas en cada momento (no se puede responder una sesión no iniciada, no se permite más de **1 contrapregunta de seguimiento por pregunta base**, no se puede emitir acta definitiva antes del cierre ni alterar turnos cerrados).
- **Ubicación:** `backend/app/domain/states/defense_session_state.py` (y estados concretos en `domain/states/`).
- **Estados formales del ciclo de vida:**
  - `DraftSessionState`: proyecto y análisis FDC asociados; pendiente de apertura en sala.
  - `OpeningGreetingState`: AURA emite saludo institucional y habilita primera pregunta base (de las 3 o 4 configuradas).
  - `AwaitingStudentAnswerState`: pregunta principal activa esperando transcripción válida (`≥ 4` palabras).
  - `AwaitingFollowUpAnswerState`: repregunta adaptativa activa (garantiza estructuralmente que tras responderla se avance a la siguiente pregunta base o al cierre, haciendo imposible un bucle infinito de repreguntas).
  - `CompletedSessionState`: nota ponderada consolidada y concepto emitido (`APROBADO`, `APLAZADO` o `NO APROBADO` si `nota ≤ 1.0`); habilita generación de acta y revisión docente.
  - `JuryValidatedState`: calificación y concepto definitivos firmados por el jurado humano (*Human-in-the-Loop*, `RF-21`).

---

### 2.4 Adapter *(Estructural)*
- **Referencia:** `refactoring.guru/design-patterns/adapter`
- **Problema real en TutoIA:** El dominio académico UTS no debe acoplarse a la sintaxis del SDK `google-genai`, ni a los formatos internos de `pypdf`/`python-docx`, ni a proveedores cambiantes de voz neuronal (TTS) y reconocimiento de voz (STT). Si mañana cambia una versión del SDK o un modelo (`gemini-3.8-flash`, `gemini-4-argon`, `gemini-3.8-flash-lite-tts`, `gemini-3.5-transcribe`), solo se modifica el adaptador correspondiente.
- **Ubicación:** Puertos en `backend/app/domain/ports/` y `frontend/src/domain/ports/`; adaptadores en `backend/app/infrastructure/` y `frontend/src/infrastructure/`.
- **Adaptadores obligatorios:**
  - **`GeminiFilesAdapter` (`AiDocumentStoragePort`)**: encapsula `client.files.upload()`, consulta de estado activo del archivo y renovación transparente desde `storage_path` si el archivo superó su ventana de retención de 48 horas en Gemini Files API, evitando reenviar el binario en cada turno de sustentación.
  - **`GeminiStructuredAnalysisAdapter` (`FdcAiAnalyzerPort` / `TurnAiEvaluatorPort`)**: encapsula el cliente oficial `google-genai` (prohibido el SDK legado deprecado `google-generativeai`), exige respuestas validadas con esquemas **Pydantic v2** (*Structured Outputs*) y traduce errores HTTP/red/cuota a excepciones tipadas de dominio (`AiProviderUnavailableError`, `AiQuotaExceededError`).
  - **`PdfDocumentAdapter` y `DocxDocumentAdapter` (`DocumentInspectorPort`)**: unifican la inspección estructural y extracción auxiliar de documentos `.pdf` y `.docx` bajo una misma interfaz.
  - **`VoiceTtsAdapter` y `VoiceSttAdapter` (`VoiceSynthesisPort`, `SpeechTranscriptionPort`)**: aíslan la generación de voz humanizada de AURA y la captura/transcripción de audio sin almacenar grabaciones biométricas permanentes (`RNF-09`).

---

### 2.5 Facade *(Estructural)*
- **Referencia:** `refactoring.guru/design-patterns/facade`
- **Problema real en TutoIA:** Tanto los controladores HTTP en backend como las vistas React en frontend tienden a degradarse en código espagueti cuando orquestan múltiples subsistemas directamente.
- **Implementación obligatoria en ambos extremos:**
  1. **Frontend — `TutoiaApiFacade`** (`frontend/src/infrastructure/facades/TutoiaApiFacade.ts`):
     - Ofrece una interfaz limpia orientada al dominio (`uploadFdcDocument()`, `getProjectAnalysis()`, `createDefenseSession()`, `startDefense()`, `submitAnswer()`, `generateEvaluationReport()`, `getSystemHealth()`).
     - Encapsula `HttpClient`, construcción de `FormData`, manejo de cabeceras, cancelación (`AbortSignal`), transformación de errores legibles y mapeo de DTOs `snake_case` a modelos TypeScript `camelCase`.
     - **Regla de bloqueo:** Cualquier aparición de `fetch(` fuera de `frontend/src/infrastructure/http/` es una violación crítica de arquitectura.
  2. **Backend — `FdcIngestionFacade` y `SustentacionFacade`** (`backend/app/application/facades/`):
     - `FdcIngestionFacade`: coordina en una sola llamada para el router el pipeline `Chain of Responsibility`, la resolución de estrategia vía `Factory Method`, el análisis multimodal con `GeminiStructuredAnalysisAdapter`, la persistencia transaccional y la emisión de eventos `Observer`.
     - `SustentacionFacade`: coordina el ciclo de vida de la sustentación (verificación de vigencia del URI en Gemini Files API, transición de `State`, evaluación por `Strategy`, generación de repreguntas y ensamblaje del acta con `Builder`).

---

### 2.6 Factory Method *(Creacional)*
- **Referencia:** `refactoring.guru/design-patterns/factory-method`
- **Problema real en TutoIA:** La plataforma debe instanciar familias coherentes de analizadores documentales y configuraciones de rúbrica según el tipo de formato (`FDC_124` Propuesta vs. `FDC_125` Informe Final) y la modalidad académica (Investigación, Desarrollo Tecnológico, Monografía, Emprendimiento).
- **Ubicación:** `backend/app/domain/factories/` (o `application/factories/` cuando inyecta puertos).
- **Fábricas obligatorias:**
  - `FdcProcessorFactory`: recibe `(fdc_type: FdcType, modality: AcademicModality)` y retorna la instancia exacta de `FdcAnalysisStrategy` junto con sus reglas de validación estructural asociadas, mediante registro declarativo (diccionario de creadores, cero cascadas `if/elif`).
  - `RubricEvaluatorFactory`: construye el evaluador configurado con los criterios ponderados vigentes en base de datos / JSON institucional y el perfil de jurado seleccionado.

---

### 2.7 Builder *(Creacional)*
- **Referencia:** `refactoring.guru/design-patterns/builder`
- **Problema real en TutoIA:** El acta institucional de sustentación UTS (`RF-20`) es un objeto complejo compuesto por múltiples secciones opcionales o progresivas: encabezado académico, síntesis del FDC evaluado, **escrito completo (transcripción íntegra) de preguntas, respuestas y contrapreguntas**, desglose cuantitativo de los 4 criterios, geometría del gráfico radar, concepto definitivo (`APROBADO` / `APLAZADO` / `NO APROBADO`), observaciones del jurado humano y cláusula ética *Human-in-the-Loop*.
- **Ubicación:** `backend/app/application/builders/report_builder.py`
- **Estructura obligatoria:**
  - `EvaluationReportBuilder`: expone pasos encadenables y explícitos:
    1. `reset(session, project)`
    2. `build_institutional_header()`
    3. `build_fdc_traceability_summary(analysis)`
    4. `build_verbatim_transcript(turns)`
    5. `build_rubric_breakdown_and_radar(scores)`
    6. `build_final_verdict(grade, verdict)`
    7. `build_human_jury_section(jury_review)`
    8. `get_result()` → produce un `EvaluationReportAggregate` limpio que luego puede renderizarse como DTO JSON para la interfaz o como documento HTML/SVG imprimible a PDF con contraste WCAG AA (`RNF-07`).

---

### 2.8 Observer *(Comportamiento)*
- **Referencia:** `refactoring.guru/design-patterns/observer`
- **Problema real en TutoIA:** Auditar tiempos de respuesta (`RNF-01`: `≤ 15 s` en análisis FDC, `≤ 8 s` por turno), registrar trazas de consumo de tokens de Gemini, guardar bitácoras de degradación al motor heurístico y alimentar el dataset anonimizado de concordancia IA vs. Jurado (`RF-22` / `OE4`) no debe acoplarse ni contaminar la lógica principal de ingesta ni de evaluación.
- **Ubicación:** Eventos y contrato `EventSubscriber` / `DomainEventPublisherPort` en `backend/app/domain/ports/`; bus y suscriptores en `backend/app/application/events/` e `infrastructure/`.
- **Eventos de dominio clave:**
  - `FdcDocumentIngestedEvent` y `FdcAnalysisCompletedEvent` (capturan `latency_ms`, `fdc_type`, `model_used`, `token_usage`, `detected_gaps_count`).
  - `DefenseTurnEvaluatedEvent` y `AiFallbackTriggeredEvent` (registran puntajes, tiempos y causa exacta si actuó el motor heurístico).
  - `DefenseCompletedEvent` y `JuryReviewRecordedEvent` (disparan actualización de estadísticas de concordancia inter-evaluador sin tocar `SustentacionFacade`).

---

## 3. Mapa Sinóptico de Integración de los 8 Patrones

```text
[Frontend UI Átomos] ──► [TutoiaApiFacade (Facade)]
                                │ HTTP /api/v1
                                ▼
             [FastAPI Router] ──► [FdcIngestionFacade / SustentacionFacade (Facade)]
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼
[Chain of Responsibility]      [FdcProcessorFactory]          [DefenseSessionState]
1. MetadataValidator             (Factory Method)                   (State)
2. Deduplication                       │                       Draft → Opening →
3. FdcStructureValidator               ▼                       AwaitingAnswer ⇄ FollowUp
4. LocalStorage                [FdcAnalysisStrategy /                   │
5. GeminiFilesUpload             EvaluationStrategy]                    ▼
        │                           (Strategy)                 Completed → JuryValidated
        ▼                               │                               │
[GeminiFilesAdapter /                   ▼                               ▼
 DocInspectorAdapter]          [GeminiStructuredAdapter]       [EvaluationReportBuilder]
     (Adapter)                        (Adapter)                       (Builder)
        └───────────────────────────────┴───────────────────────────────┘
                                        │ emite eventos
                                        ▼
                       [DomainEventBus (Observer)]
                       ├─► AuditLogSubscriber
                       ├─► LatencyMetricsSubscriber (RNF-01)
                       └─► ConcordanceExportSubscriber (OE4)
```
