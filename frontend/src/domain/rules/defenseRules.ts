import type { DefenseState, DefenseVerdict, JuryProfile } from "@/domain/models/defense";

export interface JuryProfileSelectOption {
  value: JuryProfile;
  label: string;
}

export const JURY_PROFILE_OPTIONS: ReadonlyArray<JuryProfileSelectOption> = [
  { value: "ESTANDAR_UTS", label: "Jurado Estándar UTS" },
  { value: "TECNICO_RIGUROSO", label: "Jurado Técnico Riguroso" },
];

export const JURY_PROFILE_LABELS: Record<JuryProfile, string> = {
  ESTANDAR_UTS: "Jurado Estándar UTS",
  TECNICO_RIGUROSO: "Jurado Técnico Riguroso",
};

export const DEFENSE_STATE_LABELS: Record<DefenseState, string> = {
  PREPARING: "Preparando sesión con AURA",
  AURA_SPEAKING: "AURA está formulando la pregunta",
  LISTENING_STUDENT: "AURA está escuchando tu intervención",
  EVALUATING_TURN: "Evaluando respuesta frente a la rúbrica UTS",
  COMPLETED: "Sustentación finalizada",
};

export const VERDICT_META: Record<
  DefenseVerdict,
  { label: string; badgeVariant: "success" | "warning" | "danger" }
> = {
  APROBADO: { label: "APROBADO", badgeVariant: "success" },
  APLAZADO: { label: "APLAZADO", badgeVariant: "warning" },
  NO_APROBADO: { label: "NO APROBADO", badgeVariant: "danger" },
};

export interface CriterionMeta {
  code: string;
  label: string;
  weightPercent: number;
}

export const CRITERION_META: ReadonlyArray<CriterionMeta> = [
  { code: "PERTINENCIA", label: "Pertinencia y problema", weightPercent: 30 },
  { code: "COHERENCIA", label: "Coherencia documental", weightPercent: 25 },
  { code: "FUNDAMENTACION", label: "Fundamentación teórica", weightPercent: 25 },
  { code: "METODOLOGIA", label: "Metodología y validación", weightPercent: 20 },
];

export function validateTextTurn(text: string): string | null {
  const words = text
    .trim()
    .split(/\s+/)
    .filter((word) => word.length > 0);
  if (words.length < 4) {
    return "Escriba al menos 4 palabras para evaluar su intervención con criterio académico.";
  }
  return null;
}

export function formatTurnClock(seconds: number): string {
  const safeSeconds = Math.max(0, Math.floor(seconds));
  const mins = Math.floor(safeSeconds / 60);
  const secs = safeSeconds % 60;
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

export function mapDefenseApiError(status: number, detail: string, code: string): string {
  if (code === "DEFENSE_AUDIO_UNINTELLIGIBLE") {
    return (
      detail ||
      "No fue posible reconocer voz clara en el audio. Acérquese al micrófono e intente nuevamente."
    );
  }
  if (code === "DEFENSE_TRANSCRIPT_TOO_SHORT") {
    return (
      detail ||
      "La intervención registrada fue demasiado breve (mínimo 4 palabras). Amplíe su respuesta."
    );
  }
  if (code === "DEFENSE_SESSION_NOT_FOUND") {
    return "La sesión de sustentación solicitada ya no existe o expiró.";
  }
  if (status === 409 || code === "DEFENSE_INVALID_STATE_TRANSITION") {
    return detail || "La sesión cambió de estado; sincronice la sala antes de continuar.";
  }
  if (status === 502 || code === "AI_PROVIDER_UNAVAILABLE") {
    return (
      detail ||
      "El servicio de Google Gemini presentó saturación temporal al evaluar. Puede reintentar su respuesta."
    );
  }
  if (status === 503 || code === "AI_PROVIDER_NOT_CONFIGURED") {
    return "Configure GEMINI_API_KEY en backend/.env para habilitar el diálogo y evaluación con AURA.";
  }
  return detail || "Ocurrió un error al comunicarse con la sala de sustentación.";
}
