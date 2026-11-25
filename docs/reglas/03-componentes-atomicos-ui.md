# 03 · Estándar de Componentes Atómicos UI (`presentation/components/ui/`)

> **Alcance:** Arquitectura de componentes base en `frontend/src/presentation/components/ui/`, exportación por barril (`index.ts`) y reglas de composición en vistas y orquestadores.

---

## 1. Principio de Librería UI Cerrada y Consistente

En TutoIA queda **prohibido improvisar controles de interfaz** en cada pantalla. Toda interacción estándar del usuario se construye combinando los átomos tipados y reutilizables alojados en `frontend/src/presentation/components/ui/`.

Esto garantiza:
1. **Uniformidad institucional inmediata:** cambiar el radio de borde, el anillo de foco accesible o el tono de acento UTS se hace en **un solo archivo**, propagándose a toda la plataforma.
2. **Orquestadores limpios y legibles:** vistas como `LandingPage`, `DefenseRoomPage` (`Sala`) o `JuryReviewPage` se leen como composición semántica de negocio, sin decenas de clases utilitarias repetidas ni `style={{ ... }}` inline.
3. **Accesibilidad centralizada:** atributos `aria-*`, vinculación `label ↔ id`, bloqueo de foco en modales y estados `disabled`/`loading` se resuelven una sola vez en la capa atómica.

---

## 2. Catálogo Obligatorio de Átomos Base

La carpeta `frontend/src/presentation/components/ui/` debe mantener como núcleo obligatorio los siguientes **7 átomos fundamentales** (más primitivos auxiliares de soporte como `ProgressBar` o `Alert` bajo el mismo estándar), todos re-exportados desde `index.ts`:

```text
frontend/src/presentation/components/ui/
├── Badge.tsx          # Etiquetas de estado, formato FDC y concepto evaluativo UTS
├── Button.tsx         # Acciones primarias, secundarias, contorno, fantasma y peligro
├── Card.tsx           # Contenedor institucional blanco con header, body y footer opcionales
├── FileDropzone.tsx   # Carga arrastrar-y-soltar con validación visual de PDF/DOCX y estados
├── Input.tsx          # Campo de texto/número con label, helperText, error e iconos
├── Modal.tsx          # Diálogo accesible a prueba de recorte (max-h-[90vh] + scroll interno)
├── Select.tsx         # Selector desplegable tipado con label, placeholder y estado de error
└── index.ts           # Único punto público de exportación (Barrel file)
```

### 2.1 Contrato mínimo exigido por átomo

| Átomo | Props tipadas obligatorias (TypeScript estricto) | Responsabilidad exclusiva |
| :--- | :--- | :--- |
| **`Button`** | `variant?: 'primary' \| 'secondary' \| 'outline' \| 'ghost' \| 'danger'`, `size?: 'sm' \| 'md' \| 'lg'`, `isLoading?: boolean`, `leftIcon?: ReactNode`, `rightIcon?: ReactNode`, extiende `ButtonHTMLAttributes<HTMLButtonElement>` | Renderizar acciones clicables con spinner integrado al cargar, deshabilitación automática durante `isLoading` y foco de teclado visible. |
| **`Input`** *(y variante multilínea si se requiere `Textarea` en `ui/`)* | `label?: string`, `helperText?: string`, `error?: string`, `leftAddon?: ReactNode`, `rightAddon?: ReactNode`, extiende `InputHTMLAttributes<HTMLInputElement>` | Vincular automáticamente `htmlFor` e `id` (`useId()`), mostrar borde de error accesible (`aria-invalid`, `aria-describedby`) y texto de ayuda. |
| **`Select`** | `label?: string`, `options: ReadonlyArray<{ value: string; label: string; disabled?: boolean }>`, `placeholder?: string`, `helperText?: string`, `error?: string`, extiende `SelectHTMLAttributes<HTMLSelectElement>` | Presentar listas de selección institucionales (programa académico, tipo `FDC-124`/`FDC-125`, cantidad de preguntas `3` o `4`) con estilos consistentes. |
| **`FileDropzone`** | `accept: string[]`, `maxSizeMb: number`, `selectedFile: File \| null`, `status: 'idle' \| 'dragging' \| 'uploading' \| 'analyzing' \| 'ready' \| 'error'`, `errorMessage?: string`, `onFileSelect: (file: File) => void`, `onClear?: () => void` | Gestionar selección por clic y *drag & drop*, validar formato/tamaño en cliente antes de subir, mostrar metadatos del archivo cargado y opción de reemplazo. |
| **`Badge`** | `variant?: 'neutral' \| 'brand' \| 'info' \| 'success' \| 'warning' \| 'danger'`, `size?: 'sm' \| 'md'`, `dot?: boolean`, `children: ReactNode` | Representar estados del motor IA, etiquetas `F-DC-125`, ejes temáticos y veredictos (`APROBADO` → `success`, `APLAZADO` → `warning`, `NO APROBADO` → `danger`). |
| **`Modal`** | `isOpen: boolean`, `onClose: () => void`, `title: string`, `description?: string`, `footer?: ReactNode`, `size?: 'sm' \| 'md' \| 'lg' \| 'xl'`, `closeOnBackdrop?: boolean` | Renderizar mediante Portal sobre backdrop sobrio (`bg-slate-900/40`), cerrar con `Escape`, atrapar foco y garantizar `max-h-[90vh]` con cuerpo `overflow-y-auto`. |
| **`Card`** | `title?: string`, `subtitle?: string`, `headerAction?: ReactNode`, `footer?: ReactNode`, `padding?: 'none' \| 'sm' \| 'md' \| 'lg'`, `children: ReactNode` | Estructurar secciones en superficie blanca (`bg-white border border-slate-200 rounded-xl shadow-sm`) con jerarquía limpia de encabezado y contenido. |

---

## 3. Regla de Exportación Centralizada (`index.ts`)

Todo átomo y sus tipos públicos de props deben exportarse en `frontend/src/presentation/components/ui/index.ts`:

```ts
export { Button, type ButtonProps } from "./Button";
export { Input, type InputProps } from "./Input";
export { Select, type SelectProps, type SelectOption } from "./Select";
export { FileDropzone, type FileDropzoneProps, type DropzoneStatus } from "./FileDropzone";
export { Badge, type BadgeProps, type BadgeVariant } from "./Badge";
export { Modal, type ModalProps } from "./Modal";
export { Card, type CardProps } from "./Card";
```

- **Correcto:** `import { Button, Card, FileDropzone, Select, Badge } from "@/presentation/components/ui";`
- **Prohibido:** Importaciones profundas desordenadas a archivos internos o recrear botones locales dentro de `components/fdc/` o `pages/`.

---

## 4. Prohibiciones Estrictas en Orquestadores y Componentes de Dominio

1. **Prohibido usar etiquetas nativas crudas de formulario o acción fuera de `components/ui/`:**
   - No se permiten `<button>`, `<input>`, `<select>` ni `<input type="file">` crudos en vistas orquestadoras (`Landing`, `Sala`, paneles de métricas o modales de jurado).
   - La única ubicación autorizada para envolver las etiquetas HTML nativas `<button>`, `<input>` o `<select>` es su respectivo átomo dentro de `frontend/src/presentation/components/ui/`.
2. **Prohibidos los estilos inline (`style={{ ... }}`) para diseño o maquetación:**
   - El atributo `style` solo se admite en casos estrictamente dinámicos de geometría calculada en tiempo de ejecución (p. ej., porcentaje `width: `${progress}%`` de una barra de progreso o coordenadas matemáticas de un polígono SVG del radar). Nunca para colores, márgenes, fuentes, bordes o sombras.
3. **Prohibido contaminar `components/ui/` con conocimiento del dominio TutoIA:**
   - Un átomo en `ui/` **no sabe qué es AURA, qué es un FDC-125 ni qué es una rúbrica UTS**. No importa modelos de `domain/models/` ni métodos de `TutoiaApiFacade`.
   - Si se necesita un componente específico del negocio (ej. `FdcUploadPanel` o `VerdictBadge`), ese componente se ubica en `presentation/components/fdc/` o `presentation/components/reports/` y **compone internamente** los átomos de `presentation/components/ui/`.

---

## 5. Jerarquía de Composición Permitida

```text
pages/ (LandingPage, DefenseRoomPage)
  └── compone ─► components/{fdc, defense, avatar, reports}/ (Componentes de Dominio Visual)
                    └── compone ─► components/ui/ (Átomos puros: Button, Card, FileDropzone, Modal...)
```

- Un componente en `components/ui/` **jamás** importa de `components/fdc/`, `components/defense/`, `hooks/` ni `pages/`.
- Ningún átomo de `components/ui/` puede superar las **220 líneas** de código.
