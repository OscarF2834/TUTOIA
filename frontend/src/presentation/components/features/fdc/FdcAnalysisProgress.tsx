import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import type { FdcType } from "@/domain/models/fdc";
import { Badge, Card, ProgressBar } from "@/presentation/components/ui";
import { cn } from "@/presentation/components/ui/cn";

export interface FdcAnalysisProgressProps {
  fdcType: FdcType;
  stageIndex: number;
  progressPercent: number;
}

function buildStages(fdcType: FdcType) {
  const codeLabel = fdcType === "FDC_124" ? "F-DC-124" : "F-DC-125";
  return [
    {
      title: `Validación de archivo y estructura oficial ${codeLabel}`,
      detail: "Verificando extensión, firma binaria, legibilidad y secciones mínimas UTS.",
    },
    {
      title: "Envío seguro e indexación documental",
      detail: "Registrando el documento en almacenamiento privado y Gemini Files API.",
    },
    {
      title: "Análisis semántico estructurado con Google Gemini",
      detail: "Extrayendo objetivos, metodología, matriz de coherencia y vacíos de sustentación.",
    },
  ];
}

export function FdcAnalysisProgress({
  fdcType,
  stageIndex,
  progressPercent,
}: FdcAnalysisProgressProps) {
  const stages = buildStages(fdcType);

  return (
    <Card
      title="Procesando documento institucional"
      subtitle="Este diagnóstico puede tomar entre 5 y 15 segundos según la extensión del archivo."
      headerAction={
        <Badge variant="info" dot>
          En progreso
        </Badge>
      }
    >
      <div className="space-y-5" aria-live="polite">
        <ProgressBar value={progressPercent} label="Progreso del pipeline de ingesta y análisis" tone="brand" />

        <ol className="space-y-3">
          {stages.map((stage, idx) => {
            const isDone = idx < stageIndex;
            const isCurrent = idx === stageIndex;
            return (
              <li
                key={stage.title}
                className={cn(
                  "flex items-start gap-3 rounded-lg border px-4 py-3 transition-colors",
                  isCurrent
                    ? "border-emerald-200 bg-emerald-50/50"
                    : isDone
                      ? "border-slate-200 bg-slate-50"
                      : "border-slate-200/70 bg-white opacity-60",
                )}
              >
                <span className="mt-0.5 shrink-0">
                  {isDone ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-700" />
                  ) : isCurrent ? (
                    <Loader2 className="h-4 w-4 animate-spin text-emerald-700" />
                  ) : (
                    <Circle className="h-4 w-4 text-slate-400" />
                  )}
                </span>
                <div>
                  <p className="text-sm font-semibold text-slate-900">{stage.title}</p>
                  <p className="text-xs text-slate-600">{stage.detail}</p>
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    </Card>
  );
}
