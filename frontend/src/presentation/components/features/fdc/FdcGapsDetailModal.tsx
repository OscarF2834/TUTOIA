import type { FindingStatus, GapSeverity, FdcDocumentResult } from "@/domain/models/fdc";
import {
  getAlignmentAxisLabel,
  getGapAxisLabel,
  sortGapsBySeverity,
} from "@/domain/rules/fdcFileRules";
import { Badge, Button, Modal, type BadgeVariant } from "@/presentation/components/ui";
import { cn } from "@/presentation/components/ui/cn";

export interface FdcGapsDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  result: FdcDocumentResult;
}

const FINDING_BADGE: Record<FindingStatus, BadgeVariant> = {
  SOLIDO: "success",
  PARCIAL: "warning",
  DEFICIENTE: "danger",
};

const SEVERITY_BADGE: Record<GapSeverity, BadgeVariant> = {
  ALTA: "danger",
  MEDIA: "warning",
  BAJA: "info",
};

export function FdcGapsDetailModal({ isOpen, onClose, result }: FdcGapsDetailModalProps) {
  const { analysis } = result;
  const sortedGaps = sortGapsBySeverity(analysis.detectedGaps);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="xl"
      title="Matriz de coherencia y focos de indagación para sustentación"
      description={`${result.originalFilename} · Estrategia: ${analysis.strategyName}`}
      footer={
        <Button variant="primary" onClick={onClose}>
          Entendido
        </Button>
      }
    >
      <div className="space-y-6">
        <section className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-slate-900">
              1. Matriz de coherencia documental ({analysis.coherenceFindings.length})
            </h3>
            <Badge variant="neutral" size="sm">
              Nivel global: {analysis.overallCoherenceLevel}
            </Badge>
          </div>

          <div className="space-y-3">
            {analysis.coherenceFindings.map((finding, idx) => (
              <div
                key={`${finding.alignmentAxis}-${idx}`}
                className="rounded-xl border border-slate-200 bg-slate-50/70 p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h4 className="text-sm font-semibold text-slate-900">
                    {getAlignmentAxisLabel(finding.alignmentAxis, result.fdcType)}
                  </h4>
                  <Badge variant={FINDING_BADGE[finding.status]} size="sm">
                    {finding.status}
                  </Badge>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-slate-700">{finding.analysis}</p>
                <p className="mt-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600">
                  <strong className="text-slate-800">Evidencia documental:</strong> {finding.documentEvidence}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-3 border-t border-slate-200 pt-5">
          <h3 className="text-sm font-semibold text-slate-900">
            2. Vacíos detectados y ángulos de pregunta para AURA ({sortedGaps.length})
          </h3>

          <div className="space-y-3">
            {sortedGaps.map((gap, idx) => {
              const isHigh = gap.severity === "ALTA";
              return (
                <div
                  key={`${gap.thematicAxis}-${idx}`}
                  className={cn(
                    "rounded-xl border p-4",
                    isHigh ? "border-rose-200 bg-rose-50/50" : "border-slate-200 bg-white",
                  )}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant={SEVERITY_BADGE[gap.severity]} size="sm" dot>
                        Severidad {gap.severity}
                      </Badge>
                      <span className="text-xs font-semibold text-slate-700">
                        Eje: {getGapAxisLabel(gap.thematicAxis, result.fdcType)}
                      </span>
                    </div>
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-slate-800">{gap.gapDescription}</p>
                  <div className="mt-2.5 rounded-lg border border-sky-200 bg-sky-50/70 px-3 py-2 text-xs text-sky-900">
                    <span className="font-semibold">Ángulo sugerido para AURA:</span>{" "}
                    {gap.suggestedDefenseAngle}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </Modal>
  );
}
