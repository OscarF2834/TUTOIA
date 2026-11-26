import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  Cpu,
  FilePlus2,
  ListChecks,
  ShieldAlert,
  Users,
} from "lucide-react";
import type { CoherenceLevel, FdcDocumentResult, FdcModality } from "@/domain/models/fdc";
import { FDC_TYPE_LABELS, formatFileSize, MODALITY_LABELS } from "@/domain/rules/fdcFileRules";
import { Badge, Button, Card, type BadgeVariant } from "@/presentation/components/ui";

export interface FdcAnalysisSummaryCardProps {
  result: FdcDocumentResult;
  onOpenDetails: () => void;
  onReset: () => void;
}

const COHERENCE_BADGE: Record<CoherenceLevel, BadgeVariant> = {
  ALTA: "success",
  MEDIA: "warning",
  BAJA: "danger",
};

export function FdcAnalysisSummaryCard({
  result,
  onOpenDetails,
  onReset,
}: FdcAnalysisSummaryCardProps) {
  const { project, analysis } = result;
  const syn = analysis.academicSynthesis;
  const modalityLabel = MODALITY_LABELS[project.modality as FdcModality] ?? project.modality;
  const highSeverityCount = analysis.detectedGaps.filter((g) => g.severity === "ALTA").length;

  return (
    <div className="space-y-5">
      <Card
        title={project.title}
        subtitle={`${FDC_TYPE_LABELS[result.fdcType]} · Archivo: ${result.originalFilename} (${formatFileSize(result.fileSizeBytes)})`}
        headerAction={
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={COHERENCE_BADGE[analysis.overallCoherenceLevel]} dot>
              Coherencia {analysis.overallCoherenceLevel}
            </Badge>
            <Badge variant="info">{analysis.modelName}</Badge>
          </div>
        }
        footer={
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 tabular-nums">
              <span className="inline-flex items-center gap-1.5">
                <Cpu className="h-3.5 w-3.5 text-sky-700" aria-hidden="true" />
                Latencia: <strong>{(analysis.executionMetrics.latencyMs / 1000).toFixed(2)} s</strong>
              </span>
              {(analysis.executionMetrics.inputTokens !== null ||
                analysis.executionMetrics.outputTokens !== null) && (
                <span>
                  Tokens:{" "}
                  <strong>
                    {analysis.executionMetrics.inputTokens ?? 0} in /{" "}
                    {analysis.executionMetrics.outputTokens ?? 0} out
                  </strong>
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <Button variant="outline" size="md" onClick={onReset} leftIcon={<FilePlus2 className="h-4 w-4" />}>
                Cargar otro documento
              </Button>
              <Button
                variant="secondary"
                size="md"
                onClick={onOpenDetails}
                leftIcon={<ShieldAlert className="h-4 w-4" />}
              >
                Ver matriz y vacíos ({analysis.coherenceFindings.length + analysis.detectedGaps.length})
              </Button>
            </div>
          </div>
        }
      >
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-3 rounded-xl border border-slate-200 bg-slate-50/70 p-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Programa</p>
              <p className="mt-0.5 text-sm font-medium text-slate-900">{project.academicProgram}</p>
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Modalidad</p>
              <p className="mt-0.5 text-sm font-medium text-slate-900">{modalityLabel}</p>
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Director</p>
              <p className="mt-0.5 text-sm font-medium text-slate-900">
                {project.directorName || "No especificado"}
              </p>
            </div>
            <div>
              <p className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                <Users className="h-3 w-3" aria-hidden="true" />
                Sustentantes
              </p>
              <ul className="mt-0.5 space-y-0.5 text-xs font-medium text-slate-800">
                {project.authors.map((author) => (
                  <li key={`${author.fullName}-${author.studentCode ?? "na"}`}>
                    {author.fullName}
                    {author.studentCode && (
                      <span className="tabular-nums text-slate-500"> · {author.studentCode}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {highSeverityCount > 0 && (
            <div className="flex items-center justify-between gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-xs text-amber-900">
              <span className="flex items-center gap-2 font-medium">
                <AlertCircle className="h-4 w-4 shrink-0 text-amber-700" />
                Se detectaron {highSeverityCount} vacíos de severidad ALTA relevantes para la sustentación.
              </span>
              <Button variant="ghost" size="sm" onClick={onOpenDetails} className="text-amber-900 hover:bg-amber-100">
                Revisar detalle
              </Button>
            </div>
          )}

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <div className="space-y-3">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                <BookOpen className="h-4 w-4 text-emerald-700" aria-hidden="true" />
                Problema y pregunta de investigación
              </h3>
              <p className="text-sm leading-relaxed text-slate-700">{syn.centralProblem}</p>
              {syn.researchQuestion && (
                <div className="rounded-lg border border-sky-200 bg-sky-50/60 px-3.5 py-2.5 text-xs text-sky-900">
                  <span className="font-semibold">Pregunta problema:</span> {syn.researchQuestion}
                </div>
              )}
            </div>

            <div className="space-y-3">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                <ListChecks className="h-4 w-4 text-emerald-700" aria-hidden="true" />
                Objetivo general y específicos
              </h3>
              <p className="text-sm font-medium leading-relaxed text-slate-800">{syn.generalObjective}</p>
              <ol className="list-decimal space-y-1 pl-5 text-xs leading-relaxed text-slate-700">
                {syn.specificObjectives.map((obj, index) => (
                  <li key={`${index}-${obj.slice(0, 24)}`}>{obj}</li>
                ))}
              </ol>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-5 border-t border-slate-200 pt-5 lg:grid-cols-2">
            <div className="space-y-2.5">
              <h3 className="text-sm font-semibold text-slate-900">Enfoque, fases e instrumentos</h3>
              <p className="text-xs leading-relaxed text-slate-700">{syn.researchTypeAndApproach}</p>
              {syn.phasesOrStages.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {syn.phasesOrStages.map((phase) => (
                    <Badge key={phase} variant="neutral" size="sm">
                      {phase}
                    </Badge>
                  ))}
                </div>
              )}
              {syn.technologiesAndInstruments.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {syn.technologiesAndInstruments.map((tech) => (
                    <Badge key={tech} variant="info" size="sm">
                      {tech}
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-2.5">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                <CheckCircle2 className="h-4 w-4 text-emerald-700" aria-hidden="true" />
                Resultados y conclusiones extraídas
              </h3>
              <p className="text-xs leading-relaxed text-slate-700">
                {syn.resultsAndConclusionsSummary ||
                  "Documento de propuesta (F-DC-124) o sin resultados ejecutados reportados."}
              </p>
              {syn.validationScope && (
                <p className="text-xs text-slate-600">
                  <span className="font-semibold text-slate-800">Alcance de validación:</span>{" "}
                  {syn.validationScope}
                </p>
              )}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-100/90 px-4 py-3 text-xs leading-relaxed text-slate-600">
            <strong className="text-slate-800">Supervisión humana (Human-in-the-Loop):</strong> Este
            diagnóstico automático es un insumo técnico generado por AURA y Google Gemini para orientar la
            sustentación. El veredicto académico definitivo corresponde exclusivamente al jurado docente
            designado por las UTS.
          </div>
        </div>
      </Card>
    </div>
  );
}
