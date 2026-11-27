import type { FdcType } from "@/domain/models/fdc";

export interface FdcLabelProfile {
  alignmentAxis: Record<string, string>;
  gapAxis: Record<string, string>;
  resultsSectionTitle: string;
  resultsEmptyMessage: string;
}

const ALIGNMENT_AXIS_LABELS: Record<string, string> = {
  PROBLEMA_OBJETIVOS: "Problema vs. Objetivos",
  OBJETIVOS_METODOLOGIA: "Objetivos vs. Metodología",
  METODOLOGIA_RESULTADOS: "Metodología vs. Resultados",
  MARCO_TEORICO_REFERENTES: "Marco teórico y Referentes",
};

const GAP_AXIS_LABELS: Record<string, string> = {
  CONTEXTO: "Contextualización",
  PROBLEMA: "Problema",
  FUNDAMENTACION: "Fundamentación teórica",
  METODOLOGIA: "Metodología",
  METODOLOGIA_O_PLAN: "Metodología y diseño",
  RESULTADOS: "Resultados",
  RESULTADOS_O_VALIDACION: "Resultados y conclusiones",
  CONCLUSIONES: "Conclusiones",
};

const FDC_LABEL_PROFILES: Record<FdcType, FdcLabelProfile> = {
  FDC_125: {
    alignmentAxis: ALIGNMENT_AXIS_LABELS,
    gapAxis: GAP_AXIS_LABELS,
    resultsSectionTitle: "Resultados y conclusiones extraídas",
    resultsEmptyMessage: "El informe final no reporta resultados ni conclusiones verificables.",
  },
  FDC_124: {
    alignmentAxis: {
      ...ALIGNMENT_AXIS_LABELS,
      OBJETIVOS_METODOLOGIA: "Objetivos vs. Plan de actividades",
      METODOLOGIA_RESULTADOS: "Plan de actividades vs. Resultados esperados",
    },
    gapAxis: {
      ...GAP_AXIS_LABELS,
      METODOLOGIA: "Plan de actividades y validación",
      METODOLOGIA_O_PLAN: "Plan de actividades y validación",
      RESULTADOS: "Resultados esperados",
      RESULTADOS_O_VALIDACION: "Resultados esperados",
    },
    resultsSectionTitle: "Resultados esperados",
    resultsEmptyMessage: "La propuesta no declara resultados esperados explícitos.",
  },
};

export function getAlignmentAxisLabel(axis: string, fdcType: FdcType): string {
  return FDC_LABEL_PROFILES[fdcType].alignmentAxis[axis] ?? axis;
}

export function getGapAxisLabel(axis: string, fdcType: FdcType): string {
  return FDC_LABEL_PROFILES[fdcType].gapAxis[axis] ?? axis;
}

export function getResultsSectionTitle(fdcType: FdcType): string {
  return FDC_LABEL_PROFILES[fdcType].resultsSectionTitle;
}

export function getResultsEmptyMessage(fdcType: FdcType): string {
  return FDC_LABEL_PROFILES[fdcType].resultsEmptyMessage;
}
