# Reglas Oficiales de Ingeniería — TutoIA (UTS · 2026)

> **Estado:** Normativa obligatoria y vinculante para desarrolladores humanos y agentes de IA.  
> **Proyecto:** TutoIA — Plataforma inteligente con avatar evaluador (AURA) y PLN para análisis de documentos FDC y sustentaciones de proyectos de grado (Unidades Tecnológicas de Santander · FCNI · GRIIS).  
> **Referentes:** *Clean Architecture* (Robert C. Martin), Principios **SOLID** y Catálogo Oficial de Patrones de Diseño de [Refactoring.Guru](https://refactoring.guru/design-patterns/catalog).

---

## 1. Propósito de este directorio

Esta carpeta constituye el **contrato técnico innegociable** del proyecto TutoIA. Ningún módulo nuevo, refactorización, endpoint, migración o componente visual puede fusionarse si incumple cualquiera de los documentos aquí definidos.

El objetivo es doble:
1. **Excelencia de ingeniería verificable ante el jurado de grado:** código modular, auditable, desacoplado de proveedores externos y respaldado por patrones de diseño reales (cero patrones decorativos o artificiales).
2. **Escalabilidad y mantenibilidad sostenible:** erradicar archivos monolíticos («código espagueti»), estilos improvisados y acoplamientos directos con SDKs de terceros o llamadas `fetch` dispersas.

---

## 2. Índice de documentos normativos

| Orden | Archivo | Alcance obligatorio | ¿Cuándo consultarlo? |
| :---: | :--- | :--- | :--- |
| **01** | [`01-arquitectura-y-srp.md`](./01-arquitectura-y-srp.md) | Mapa oficial de capas en `backend/app/` y `frontend/src/`, Regla de Dependencia, Principio de Responsabilidad Única (SRP) y límites estrictos de líneas por archivo (`250–350` máx.). | Antes de crear cualquier carpeta, módulo, servicio, entidad, repositorio, hook o página. |
| **02** | [`02-patrones-refactoring-guru.md`](./02-patrones-refactoring-guru.md) | Inventario oficial de 8 patrones de Refactoring.Guru acoplados al dominio real de TutoIA (`Chain of Responsibility`, `Strategy`, `State`, `Adapter`, `Facade`, `Factory Method`, `Builder`, `Observer`). | Antes de escribir lógica condicional (`if/elif/switch`), integrar SDKs externos (`google-genai`, STT/TTS) o diseñar flujos de negocio. |
| **03** | [`03-componentes-atomicos-ui.md`](./03-componentes-atomicos-ui.md) | Estándar de librería cerrada de átomos en `frontend/src/presentation/components/ui/` exportados desde `index.ts` y prohibición de controles HTML crudos en vistas orquestadoras. | Antes de construir o editar cualquier formulario, pantalla, modal, tarjeta o zona de carga en React. |
| **04** | [`04-diseno-frontend-academico.md`](./04-diseno-frontend-academico.md) | Sistema visual institucional *Academic SaaS* (luminoso, formal, `slate-50/100`, acento sobrio UTS), accesibilidad WCAG AA, modales `max-h-[90vh]` y estados UX de ingesta/evaluación. | Al aplicar clases de Tailwind CSS, diseñar layouts, estados de carga FDC, barras de progreso o reportes de evaluación. |

---

## 3. La Regla de Oro Anti-Espagueti

> **«Cada unidad de código tiene una única razón para cambiar, habita en una sola capa arquitectónica, respeta su presupuesto de tamaño y delega toda variación de comportamiento al patrón de diseño que le corresponde.»**

Para hacer cumplir esta Regla de Oro, todo cambio en el repositorio se somete a **6 mandamientos de cumplimiento estricto**:

### M1 · Cero lógica de negocio en bordes de entrada o vistas
- En **Backend**, los routers de FastAPI (`presentation/`) solo validan esquemas HTTP de entrada, invocan una fachada o caso de uso de `application/` y devuelven un DTO tipado. Jamás ejecutan consultas SQL, llamadas a Gemini ni cálculos de rúbrica.
- En **Frontend**, las páginas orquestadoras (`LandingPage`, `DefenseRoomPage`, etc.) solo coordinan composición visual y delegan efectos/estado a custom hooks que consumen `TutoiaApiFacade`.

### M2 · Cero dependencias externas fuera de `infrastructure/`
- Está **terminantemente prohibido** importar `google.genai`, `sqlalchemy`, `pypdf`, `docx` o clientes HTTP externos dentro de `domain/` o `application/`.
- Está **terminantemente prohibido** invocar `fetch()`, `XMLHttpRequest`, `WebSocket` o APIs crudas de audio del navegador directamente desde componentes React o hooks de `presentation/`. Todo pasa por `TutoiaApiFacade` o adaptadores en `frontend/src/infrastructure/`.

### M3 · Cero cascadas `if/elif/else` de negocio
- Si necesitas ramificar el comportamiento según el tipo de formato (`FDC-124` vs. `FDC-125`), la modalidad de grado, el perfil del jurado, el estado de la sustentación o el motor de evaluación, **no agregues otro `elif`**: extiende el patrón oficial asignado en [`02-patrones-refactoring-guru.md`](./02-patrones-refactoring-guru.md) (`Strategy`, `Factory Method`, `State` o `Chain of Responsibility`).

### M4 · Cero patrones decorativos (*Anti-Overengineering*)
- Ninguna clase `Factory`, `Builder` o `Strategy` puede crearse «por si acaso» con una sola línea trivial sin propósito. Cada patrón implementado debe resolver una frontera de cambio real del dominio UTS documentada en la arquitectura.

### M5 · Presupuesto duro de líneas y complejidad
- **Objetivo saludable:** `≤ 250 líneas` por archivo.
- **Tope duro máximo:** `350 líneas` por archivo (cualquier archivo que supere las 250 líneas exige revisión de cohesión; superar 350 líneas bloquea la entrega y obliga a particionar responsabilidades).
- **Funciones/métodos:** máximo `40 líneas` efectivas y máximo `3 niveles` de indentación.

### M6 · Cero controles HTML crudos ni estética informal en UI
- Todo botón, campo de texto, selector, dropzone de archivos, insignia, modal o tarjeta se consume desde `frontend/src/presentation/components/ui/index.ts`.
- La interfaz respeta rigurosamente el estilo **Academic SaaS institucional** (luminoso, formal y accesible), erradicando cualquier rastro de estética neón/cyberpunk o estilos `style={{ ... }}` improvisados.

---

## 4. Lista de verificación previa a cada entrega (*Definition of Done*)

Antes de dar por completada cualquier tarea o módulo en TutoIA, verifica:

- [ ] ¿Todas las importaciones respetan la dirección de capas definida en `01-arquitectura-y-srp.md`?
- [ ] ¿Ningún archivo nuevo o modificado supera el umbral de 250–350 líneas?
- [ ] ¿Los SDKs externos (`google-genai`, SQLAlchemy, lectores PDF/DOCX, voz) están encapsulados tras un `Port` en `domain/` y un `Adapter` en `infrastructure/`?
- [ ] ¿Las validaciones encadenadas, variaciones de rúbrica/FDC y estados de sesión usan los patrones de `02-patrones-refactoring-guru.md` en lugar de banderas booleanas y `if/else` anidados?
- [ ] ¿El frontend usa exclusivamente `TutoiaApiFacade` (cero `fetch` directo) y átomos de `presentation/components/ui/`?
- [ ] ¿La interfaz cumple la paleta académica `slate-50/100` + tarjetas blancas + acento sobrio UTS, contraste WCAG AA y modales con `max-h-[90vh]`?
