import type {
  CoherenceLevel,
  FdcDocumentResult,
  FdcType,
  FindingStatus,
  GapSeverity,
} from "@/domain/models/fdc";

export interface FdcDocumentResponseDto {
  document_id: string;
  project_id: string;
  analysis_id: string;
  fdc_type: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  ingestion_status: string;
  gemini_file_uri: string | null;
  created_at: string;
  project: {
    title: string;
    academic_program: string;
    modality: string;
    authors: Array<{ full_name: string; student_code: string | null }>;
    director_name: string | null;
  };
  analysis: {
    strategy_name: string;
    model_name: string;
    schema_version: string;
    overall_coherence_level: string;
    academic_synthesis: {
      central_problem: string;
      research_question: string | null;
      justification_summary: string;
      general_objective: string;
      specific_objectives: string[];
      research_type_and_approach: string;
      phases_or_stages: string[];
      technologies_and_instruments: string[];
      validation_scope: string | null;
      results_and_conclusions_summary: string | null;
    };
    coherence_findings: Array<{
      alignment_axis: string;
      status: string;
      analysis: string;
      document_evidence: string;
    }>;
    detected_gaps: Array<{
      thematic_axis: string;
      severity: string;
      gap_description: string;
      suggested_defense_angle: string;
    }>;
    execution_metrics: {
      latency_ms: number;
      input_tokens: number | null;
      output_tokens: number | null;
    };
  };
}

export function mapFdcResponseDtoToDomain(dto: FdcDocumentResponseDto): FdcDocumentResult {
  const syn = dto.analysis.academic_synthesis;
  return {
    documentId: dto.document_id,
    projectId: dto.project_id,
    analysisId: dto.analysis_id,
    fdcType: dto.fdc_type as FdcType,
    originalFilename: dto.original_filename,
    mimeType: dto.mime_type,
    fileSizeBytes: dto.file_size_bytes,
    ingestionStatus: dto.ingestion_status,
    geminiFileUri: dto.gemini_file_uri,
    createdAt: dto.created_at,
    project: {
      title: dto.project.title,
      academicProgram: dto.project.academic_program,
      modality: dto.project.modality,
      authors: dto.project.authors.map((a) => ({
        fullName: a.full_name,
        studentCode: a.student_code,
      })),
      directorName: dto.project.director_name,
    },
    analysis: {
      strategyName: dto.analysis.strategy_name,
      modelName: dto.analysis.model_name,
      schemaVersion: dto.analysis.schema_version,
      overallCoherenceLevel: dto.analysis.overall_coherence_level as CoherenceLevel,
      academicSynthesis: {
        centralProblem: syn.central_problem,
        researchQuestion: syn.research_question,
        justificationSummary: syn.justification_summary,
        generalObjective: syn.general_objective,
        specificObjectives: syn.specific_objectives,
        researchTypeAndApproach: syn.research_type_and_approach,
        phasesOrStages: syn.phases_or_stages,
        technologiesAndInstruments: syn.technologies_and_instruments,
        validationScope: syn.validation_scope,
        resultsAndConclusionsSummary: syn.results_and_conclusions_summary,
      },
      coherenceFindings: dto.analysis.coherence_findings.map((f) => ({
        alignmentAxis: f.alignment_axis,
        status: f.status as FindingStatus,
        analysis: f.analysis,
        documentEvidence: f.document_evidence,
      })),
      detectedGaps: dto.analysis.detected_gaps.map((g) => ({
        thematicAxis: g.thematic_axis,
        severity: g.severity as GapSeverity,
        gapDescription: g.gap_description,
        suggestedDefenseAngle: g.suggested_defense_angle,
      })),
      executionMetrics: {
        latencyMs: dto.analysis.execution_metrics.latency_ms,
        inputTokens: dto.analysis.execution_metrics.input_tokens,
        outputTokens: dto.analysis.execution_metrics.output_tokens,
      },
    },
  };
}
