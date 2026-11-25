# 01 · Arquitectura Limpia, Mapa de Capas y Responsabilidad Única (SRP)

> **Alcance:** Estructura obligatoria de directorios, dirección de dependencias y umbrales de cohesión para `backend/app/` y `frontend/src/`.

---

## 1. Principio Rector: Separación Estricta de Capas

TutoIA adopta **Clean Architecture** combinada con los principios **SOLID** (especialmente **S**RP — *Single Responsibility Principle* y **D**IP — *Dependency Inversion Principle*):

1. **La lógica de negocio académica UTS es soberana:** Las reglas de calificación (`0.0` a `5.0`), ponderación de criterios, emisión de conceptos (`APROBADO`, `APLAZADO`, `NO APROBADO` para notas críticas `≤ 1.0`), límites de contrapreguntas y estructura exigida de los formatos FDC viven en `domain/` sin depender de frameworks web, bases de datos ni proveedores de IA.
2. **Inversión de Dependencias (DIP):** Cuando un caso de uso necesita analizar un PDF con Gemini o guardar en PostgreSQL, invoca un **Puerto** (`Protocol` o `ABC` declarado en `domain/ports/`). La implementación concreta vive en `infrastructure/` e inyecta sus dependencias desde el borde de composición.

---

## 2. Mapa Oficial de Capas en Backend (`backend/app/`)

### 2.1 Flujo de ejecución vs. dependencia de código

- **Flujo de ejecución en tiempo de corrida (Request → Persistencia/IA):**  
  `presentation/` → `application/` → `domain/` → `infrastructure/` *(resuelto en tiempo de ejecución mediante puertos inyectados)*.
- **Regla de importación estática (Compilación / Imports):**  
  `domain/` **no importa nada** de `application/`, `presentation/` ni `infrastructure/`. `infrastructure/` implementa los contratos de `domain/ports/`.

```text
backend/app/
├── presentation/                 # Borde HTTP (FastAPI): routers, DTOs HTTP, middlewares
│   ├── api/
│   │   ├── dependencies.py       # Composición e inyección de dependencias (DI)
│   │   └── v1/
│   │       ├── routers/          # Endpoints delgados por recurso (fdc, sessions, reports)
│   │       └── schemas/          # Modelos Pydantic exclusivos de Request/Response HTTP
│   └── exception_handlers.py     # Traducción DomainException → HTTPException (400/404/409/422/503)
│
├── application/                  # Orquestación de casos de uso y flujos del sistema
│   ├── facades/                  # SustentacionFacade, FdcIngestionFacade
│   ├── use_cases/                # Casos de uso atómicos (IngestFdcUseCase, EvaluateTurnUseCase...)
│   ├── pipelines/                # Eslabones de Chain of Responsibility de ingesta/validación
│   ├── builders/                 # ReportBuilder para actas y escritos completos de sesión
│   ├── events/                   # Bus de eventos y suscriptores de aplicación (Observer)
│   └── dtos/                     # Objetos de transferencia internos entre capas
│
├── domain/                       # Núcleo puro de negocio UTS (CERO frameworks externos)
│   ├── entities/                 # Project, FdcDocument, FdcAnalysis, DefenseSession, Turn, Rubric
│   ├── value_objects/            # Grade, Verdict, FdcType, AcademicModality, CriterionScore
│   ├── ports/                    # Contratos ABC/Protocol (Repositorios, AiEnginePort, FileStorePort, VoicePort)
│   ├── strategies/               # Contratos y políticas de análisis FDC y evaluación por rúbrica
│   ├── factories/                # Fábricas de dominio/aplicación para procesadores FDC y rúbricas
│   ├── states/                   # Máquina de estados formal de la sesión de sustentación
│   └── exceptions/               # Excepciones semánticas del dominio (InvalidFdcFormatError, etc.)
│
└── infrastructure/               # Detalles técnicos, SDKs externos y persistencia
    ├── config/                   # Variables de entorno tipadas (pydantic-settings)
    ├── persistence/              # SQLAlchemy 2.0 (modelos ORM, sesión async/sync, repositorios, Alembic)
    ├── ai/                       # Adaptadores de Google Gemini (google-genai, Files API, Structured Outputs)
    │                             # + Adaptador heurístico local de contingencia
    ├── documents/                # Adaptadores de inspección PDF/DOCX y almacenamiento local seguro
    └── voice/                    # Adaptadores externos de síntesis neuronal (TTS) y transcripción (STT)
```

### 2.2 Matriz de permisos de importación (Backend)

| Capa origen | Puede importar de | PROHIBIDO importar de |
| :--- | :--- | :--- |
| `domain/` | Librería estándar Python (`dataclasses`, `enum`, `abc`, `typing`, `uuid`, `datetime`, `decimal`) | `fastapi`, `sqlalchemy`, `google.genai`, `pypdf`, `docx`, `application/`, `presentation/`, `infrastructure/` |
| `application/` | `domain/`, librería estándar, `pydantic` (solo para DTOs/esquemas agnósticos de contrato) | `fastapi`, `sqlalchemy`, `google.genai`, `presentation/`, clases concretas de `infrastructure/` |
| `infrastructure/` | `domain/` (entidades, puertos, excepciones), `application/dtos`, SDKs externos (`sqlalchemy`, `google.genai`, `pypdf`, `docx`) | `presentation/` (`fastapi.Request`, `UploadFile` crudo de FastAPI, routers) |
| `presentation/` | `application/` (fachadas, casos de uso, DTOs), `domain/exceptions`, `infrastructure/config` y `dependencies.py` (solo para cableado DI) | Consultas directas a `sqlalchemy` o llamadas directas a `google.genai` dentro de routers |

> **Nota sobre compatibilidad PostgreSQL / SQLite:** En `infrastructure/persistence/`, toda columna estructurada (rúbricas, hallazgos FDC, métricas de tokens) debe usar un tipo adaptable `JSON().with_variant(JSONB(), "postgresql")` de SQLAlchemy 2.0 para aprovechar `JSONB` nativo en producción (PostgreSQL) manteniendo ejecución local inmediata en SQLite y `pytest`.

---

## 3. Mapa Oficial de Capas en Frontend (`frontend/src/`)

El flujo arquitectónico del cliente separa modelos y contratos puros (`domain/`), comunicación y adaptadores del navegador (`infrastructure/`), e interfaz visual React (`presentation/`):

```text
frontend/src/
├── domain/                       # Modelos TypeScript puros y reglas de negocio en cliente
│   ├── models/                   # Project.ts, FdcDocument.ts, FdcAnalysis.ts, DefenseSession.ts, Rubric.ts
│   ├── ports/                    # TutoiaApiPort.ts, VoiceEnginePort.ts
│   └── rules/                    # Reglas puras (validación previa de extensión/tamaño, formateo de notas)
│
├── infrastructure/               # Adaptadores HTTP, Fachada de API y APIs del navegador
│   ├── http/                     # HttpClient.ts (manejo centralizado de errores HTTP, timeouts y JSON/FormData)
│   ├── mappers/                  # Transformadores snake_case (API DTO) ↔ camelCase (Domain Model)
│   ├── facades/                  # TutoiaApiFacade.ts (ÚNICO punto de acceso del frontend hacia el backend)
│   └── voice/                    # Adaptadores de micrófono (MediaRecorder/STT) y reproducción de audio (TTS)
│
└── presentation/                 # Capa visual en React + TypeScript + Tailwind CSS
    ├── components/
    │   ├── ui/                   # Librería cerrada de átomos reutilizables (exportados en index.ts)
    │   ├── fdc/                  # Componentes de dominio para carga, progreso y resumen de análisis FDC
    │   ├── defense/              # Sala en vivo, folio de transcripción, radar de criterios
    │   ├── avatar/               # AvatarAURA (SVG reactivo a estados visuales puros)
    │   └── reports/              # Visualización de acta, veredicto y validación Human-in-the-Loop
    ├── hooks/                    # Custom hooks orquestadores (useFdcUpload, useDefenseSession)
    ├── pages/                    # Vistas de nivel ruta delgadas (LandingPage, DefenseRoomPage, JuryPage)
    └── layouts/                  # Marcos institucionales (AcademicHeader, MainShell)
```

### 3.1 Matriz de permisos de importación (Frontend)

| Capa origen | Puede importar de | PROHIBIDO importar de |
| :--- | :--- | :--- |
| `domain/` | Solo archivos propios de `domain/` (TypeScript puro) | `react`, `react-dom`, `fetch`, `window`, `localStorage`, `infrastructure/`, `presentation/` |
| `infrastructure/` | `domain/` (modelos y puertos), APIs Web (`fetch`, `FormData`, `AudioContext`, `MediaRecorder`) | `react`, hooks, componentes JSX/TSX de `presentation/` |
| `presentation/` | `domain/models`, `domain/rules`, `infrastructure/facades/TutoiaApiFacade` (y adaptadores inyectados en hooks) | `fetch` directo, `HttpClient` crudo, DTOs `snake_case` sin mapear |

---

## 4. Reglas de Responsabilidad Única (SRP) y Límites de Tamaño

### 4.1 Presupuesto cuantitativo por archivo

| Tipo de artefacto | Objetivo ideal | Límite máximo permitido | Acción obligatoria al exceder |
| :--- | :---: | :---: | :--- |
| Router FastAPI (`routers/*.py`) | `80 – 150` líneas | **200 líneas** | Dividir por sub-recurso o mover mapeos/validaciones a `schemas/` y `facades/`. |
| Caso de Uso / Handler / Estrategia | `80 – 200` líneas | **250 líneas** | Extraer pasos auxiliares en colaboradores cohesivos o políticas de dominio. |
| Adaptador (`Gemini*Adapter`, Repositorio ORM) | `120 – 250` líneas | **320 líneas** | Separar cliente base, mappers de persistencia/esquemas y prompts estructurados. |
| Átomo UI (`components/ui/*.tsx`) | `50 – 160` líneas | **220 líneas** | Extraer subcomponentes internos o tabla de variantes en constantes locales. |
| Página u Orquestador (`pages/*.tsx`) | `100 – 200` líneas | **250 líneas** | Extraer estado a un custom hook en `hooks/` y bloques visuales a `components/<dominio>/`. |
| **Cualquier archivo de código fuente** | **≤ 250 líneas** | **350 líneas (tope duro)** | **Refactorización obligatoria inmediata antes de continuar.** |

### 4.2 Prueba del «Y» para detectar violaciones de SRP

Formula en una sola oración qué hace tu clase, módulo o componente. **Si necesitas usar la conjunción «Y» entre dos niveles de abstracción distintos, viola SRP y debe dividirse:**

- **Incorrecto (Espagueti):** *«`upload_fdc.py` recibe el archivo multipart, verifica que sea PDF válido, extrae su texto, lo sube a Gemini Files API, ejecuta el prompt de análisis Y guarda el resultado en PostgreSQL.»*
- **Correcto (SRP + Clean Architecture):**
  - `fdc_router.py` recibe la petición HTTP y delega a `FdcIngestionFacade`.
  - El pipeline `Chain of Responsibility` valida metadatos, estructura e indexa en Gemini.
  - `GeminiFdcAnalyzerAdapter` solicita la extracción estructurada a `google-genai`.
  - `Fdc125FinalReportStrategy` aplica las reglas académicas de coherencia del formato F-DC-125.
  - `SqlAlchemyFdcRepository` persiste la transacción en base de datos.

### 4.3 Reglas adicionales de higiene de código

1. **Un concepto principal por archivo:** Una entidad de dominio principal, un caso de uso, una estrategia concreta o un componente React exportado por archivo.
2. **Prompts de IA fuera de los adaptadores:** Las instrucciones del sistema (*system instructions*) y plantillas de evaluación no se incrustan como cadenas gigantes dentro de métodos Python; se organizan en módulos dedicados de plantillas versionadas bajo `infrastructure/ai/prompts/` o son provistas por la `Strategy` correspondiente.
3. **Tipado estático al 100 %:** En Python (`mypy`/`pyright` compatible, anotaciones completas en firmas públicas, cero `dict[str, Any]` para contratos de negocio) y en TypeScript (`strict: true`, **prohibido el uso de `any`**).
