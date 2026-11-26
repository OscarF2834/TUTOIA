import type { DefenseGap, FdcErrorInfo, FdcModality, FdcType } from "@/domain/models/fdc";

export const MAX_FDC_FILE_SIZE_MB = 20;
export const MAX_FDC_FILE_SIZE_BYTES = MAX_FDC_FILE_SIZE_MB * 1024 * 1024;
export const ALLOWED_FDC_EXTENSIONS = [".pdf", ".docx"] as const;

export const FDC_TYPE_LABELS: Record<FdcType, string> = {
  FDC_124: "F-DC-124 · Propuesta de Trabajo de Grado",
  FDC_125: "F-DC-125 · Informe Final de Trabajo de Grado",
};

export const MODALITY_LABELS: Record<FdcModality, string> = {
  DESARROLLO_TECNOLOGICO: "Desarrollo Tecnológico",
  INVESTIGACION: "Proyecto de Investigación",
  MONOGRAFIA: "Monografía",
  EMPRENDIMIENTO: "Emprendimiento",
};

export const SECTION_LABELS: Record<string, string> = {
  problema: "Descripción / Planteamiento del problema",
  objetivos: "Objetivo general y objetivos específicos",
  justificacion_o_fundamento: "Justificación, Estado del arte o Fundamento teórico",
  plan_o_metodologia: "Plan de actividades, Cronograma, Resultados esperados o Metodología",
  diseno_o_metodologia: "Diseño de la investigación, Desarrollo del trabajo de grado o Metodología",
  resultados: "Resultados",
  conclusiones: "Conclusiones",
};

export const ALIGNMENT_AXIS_LABELS: Record<string, string> = {
  PROBLEMA_OBJETIVOS: "Problema vs. Objetivos",
  OBJETIVOS_METODOLOGIA: "Objetivos vs. Metodología",
  METODOLOGIA_RESULTADOS: "Metodología vs. Resultados",
  MARCO_TEORICO_REFERENTES: "Marco teórico y Referentes",
};

export const GAP_AXIS_LABELS: Record<string, string> = {
  CONTEXTO: "Contextualización",
  PROBLEMA: "Problema",
  FUNDAMENTACION: "Fundamentación teórica",
  METODOLOGIA: "Metodología",
  RESULTADOS: "Resultados",
  CONCLUSIONES: "Conclusiones",
};

const SEVERITY_ORDER: Record<DefenseGap["severity"], number> = {
  ALTA: 0,
  MEDIA: 1,
  BAJA: 2,
};

export function validateFdcFile(file: File): string | null {
  const lowerName = file.name.toLowerCase();
  const hasAllowedExtension = ALLOWED_FDC_EXTENSIONS.some((ext) => lowerName.endsWith(ext));
  if (!hasAllowedExtension) {
    return "Formato no admitido. Seleccione un documento institucional en formato .pdf o .docx.";
  }
  if (file.size <= 0) {
    return "El archivo seleccionado está vacío (0 bytes).";
  }
  if (file.size > MAX_FDC_FILE_SIZE_BYTES) {
    return `El archivo supera el límite máximo permitido de ${MAX_FDC_FILE_SIZE_MB} MB.`;
  }
  return null;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export function sortGapsBySeverity(gaps: DefenseGap[]): DefenseGap[] {
  return [...gaps].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);
}

export function mapApiErrorToUserFeedback(
  status: number,
  detail: string,
  code: string,
  context?: Record<string, unknown>,
): FdcErrorInfo {
  if (status === 413 || code === "FDC_FILE_TOO_LARGE") {
    return {
      status,
      code,
      title: "Archivo demasiado grande",
      message: detail || `El documento excede el límite institucional de ${MAX_FDC_FILE_SIZE_MB} MB.`,
      canRetry: false,
    };
  }
  if (status === 415 || code === "FDC_UNSUPPORTED_FORMAT") {
    return {
      status,
      code,
      title: "Formato documental no soportado",
      message: detail || "Cargue un archivo válido en formato PDF (.pdf) o Word (.docx).",
      canRetry: false,
    };
  }
  if (status === 422 && code === "FDC_INVALID_STRUCTURE") {
    const rawMissing = Array.isArray(context?.missing_sections) ? context.missing_sections : [];
    const missingSections = rawMissing.filter((item): item is string => typeof item === "string");
    const fdcType = typeof context?.fdc_type === "string" ? context.fdc_type : undefined;
    return {
      status,
      code,
      title: `Estructura incompleta para ${fdcType === "FDC_124" ? "F-DC-124" : "F-DC-125"}`,
      message:
        detail ||
        "El documento no contiene todas las secciones mínimas exigidas por el formato seleccionado.",
      missingSections,
      fdcType,
      canRetry: false,
    };
  }
  if (status === 422) {
    return {
      status,
      code,
      title: "No fue posible leer el documento FDC",
      message: detail || "El archivo está vacío, dañado o escaneado sin texto seleccionable.",
      canRetry: false,
    };
  }
  if (status === 502 || code === "AI_PROVIDER_UNAVAILABLE" || code === "AI_RESPONSE_VALIDATION_ERROR") {
    return {
      status,
      code,
      title: "Saturación temporal del servicio de IA",
      message:
        detail ||
        "Los modelos de Google Gemini agotaron los reintentos por alta demanda temporal. Intente nuevamente.",
      canRetry: true,
    };
  }
  if (status === 503 || code === "AI_PROVIDER_NOT_CONFIGURED") {
    return {
      status,
      code,
      title: "Motor Gemini no configurado",
      message:
        detail ||
        "Configure GEMINI_API_KEY en backend/.env para habilitar el análisis multimodal del documento.",
      canRetry: false,
    };
  }
  return {
    status,
    code,
    title: "Error al procesar el documento FDC",
    message: detail || "Ocurrió un error inesperado al comunicarse con el servidor.",
    canRetry: status === 0 || status >= 500,
  };
}
