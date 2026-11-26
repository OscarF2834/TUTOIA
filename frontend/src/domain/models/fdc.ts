export type FdcType = "FDC_124" | "FDC_125";

export type FdcModality =
  | "DESARROLLO_TECNOLOGICO"
  | "INVESTIGACION"
  | "MONOGRAFIA"
  | "EMPRENDIMIENTO";

export type CoherenceLevel = "ALTA" | "MEDIA" | "BAJA";
export type FindingStatus = "SOLIDO" | "PARCIAL" | "DEFICIENTE";
export type GapSeverity = "ALTA" | "MEDIA" | "BAJA";

export interface ProjectAuthor {
  fullName: string;
  studentCode: string | null;
}

export interface ProjectSummary {
  title: string;
  academicProgram: string;
  modality: FdcModality | string;
  authors: ProjectAuthor[];
  directorName: string | null;
}

export interface AcademicSynthesis {
  centralProblem: string;
  researchQuestion: string | null;
  justificationSummary: string;
  generalObjective: string;
  specificObjectives: string[];
  researchTypeAndApproach: string;
  phasesOrStages: string[];
  technologiesAndInstruments: string[];
  validationScope: string | null;
  resultsAndConclusionsSummary: string | null;
}

export interface CoherenceFinding {
  alignmentAxis: string;
  status: FindingStatus;
  analysis: string;
  documentEvidence: string;
}

export interface DefenseGap {
  thematicAxis: string;
  severity: GapSeverity;
  gapDescription: string;
  suggestedDefenseAngle: string;
}

export interface ExecutionMetrics {
  latencyMs: number;
  inputTokens: number | null;
  outputTokens: number | null;
}

export interface FdcAnalysisDetail {
  strategyName: string;
  modelName: string;
  schemaVersion: string;
  overallCoherenceLevel: CoherenceLevel;
  academicSynthesis: AcademicSynthesis;
  coherenceFindings: CoherenceFinding[];
  detectedGaps: DefenseGap[];
  executionMetrics: ExecutionMetrics;
}

export interface FdcDocumentResult {
  documentId: string;
  projectId: string;
  analysisId: string;
  fdcType: FdcType;
  originalFilename: string;
  mimeType: string;
  fileSizeBytes: number;
  ingestionStatus: string;
  geminiFileUri: string | null;
  createdAt: string;
  project: ProjectSummary;
  analysis: FdcAnalysisDetail;
}

export interface FdcUploadRequest {
  file: File;
  fdcType: FdcType;
  academicProgram?: string;
  modality?: FdcModality | "";
}

export interface FdcErrorInfo {
  status: number;
  code: string;
  title: string;
  message: string;
  missingSections?: string[];
  fdcType?: string;
  canRetry: boolean;
}
