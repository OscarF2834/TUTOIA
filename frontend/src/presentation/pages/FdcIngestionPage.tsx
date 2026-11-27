import { useState } from "react";
import { GraduationCap } from "lucide-react";
import type { JuryProfile } from "@/domain/models/defense";
import { Badge, Card } from "@/presentation/components/ui";
import { FdcAnalysisProgress } from "@/presentation/components/features/fdc/FdcAnalysisProgress";
import { FdcAnalysisSummaryCard } from "@/presentation/components/features/fdc/FdcAnalysisSummaryCard";
import { FdcErrorAlert } from "@/presentation/components/features/fdc/FdcErrorAlert";
import { FdcGapsDetailModal } from "@/presentation/components/features/fdc/FdcGapsDetailModal";
import { FdcUploadForm } from "@/presentation/components/features/fdc/FdcUploadForm";
import { useFdcIngestion } from "@/presentation/hooks/useFdcIngestion";

export interface FdcIngestionPageProps {
  onStartDefense?: (documentId: string, juryProfile: JuryProfile) => void;
}

export default function FdcIngestionPage({ onStartDefense }: FdcIngestionPageProps) {
  const {
    status,
    stageIndex,
    progressPercent,
    activeFdcType,
    result,
    error,
    submitUpload,
    retryLastUpload,
    resetForNewUpload,
  } = useFdcIngestion();
  const [detailsOpen, setDetailsOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <header className="mb-7 flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
          <div className="flex items-center gap-3.5">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-700 text-white shadow-sm">
              <GraduationCap className="h-6 w-6" aria-hidden="true" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl font-semibold tracking-tight text-slate-900">
                  TutoIA · Evaluación Documental FDC
                </h1>
                <Badge variant="brand" size="sm">
                  UTS · FCNI · GRIIS
                </Badge>
              </div>
              <p className="text-sm text-slate-600">
                Análisis estructurado de Propuestas (F-DC-124) e Informes Finales (F-DC-125) con Google Gemini.
              </p>
            </div>
          </div>
        </header>

        <main className="space-y-6">
          {status === "hydrating" && (
            <Card>
              <p className="text-sm text-slate-600">
                Recuperando el último análisis documental guardado en esta sesión…
              </p>
            </Card>
          )}

          {status !== "success" && status !== "hydrating" && (
            <FdcUploadForm isSubmitting={status === "analyzing"} onSubmit={submitUpload} />
          )}

          {status === "analyzing" && (
            <FdcAnalysisProgress
              fdcType={activeFdcType}
              stageIndex={stageIndex}
              progressPercent={progressPercent}
            />
          )}

          {status === "error" && error && (
            <FdcErrorAlert error={error} onRetry={retryLastUpload} />
          )}

          {status === "success" && result && (
            <>
              <FdcAnalysisSummaryCard
                result={result}
                onOpenDetails={() => setDetailsOpen(true)}
                onReset={() => {
                  setDetailsOpen(false);
                  resetForNewUpload();
                }}
                onStartDefense={
                  onStartDefense
                    ? (juryProfile) => onStartDefense(result.documentId, juryProfile)
                    : undefined
                }
              />
              <FdcGapsDetailModal
                isOpen={detailsOpen}
                onClose={() => setDetailsOpen(false)}
                result={result}
              />
            </>
          )}
        </main>
      </div>
    </div>
  );
}
