import { AlertTriangle, RotateCcw } from "lucide-react";
import type { FdcErrorInfo } from "@/domain/models/fdc";
import { SECTION_LABELS } from "@/domain/rules/fdcFileRules";
import { Badge, Button, Card } from "@/presentation/components/ui";

export interface FdcErrorAlertProps {
  error: FdcErrorInfo;
  onRetry?: () => void;
}

export function FdcErrorAlert({ error, onRetry }: FdcErrorAlertProps) {
  const hasMissingSections = Boolean(error.missingSections && error.missingSections.length > 0);

  return (
    <Card className="border-rose-200 bg-rose-50/50">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-rose-100 text-rose-700">
            <AlertTriangle className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-semibold text-rose-900">{error.title}</h3>
              <Badge variant="danger" size="sm">
                {error.status > 0 ? `HTTP ${error.status} · ${error.code}` : error.code}
              </Badge>
            </div>
            <p className="text-sm leading-relaxed text-rose-800">{error.message}</p>

            {hasMissingSections && (
              <div className="rounded-lg border border-rose-200 bg-white/90 p-3">
                <p className="text-xs font-semibold text-slate-800">
                  Secciones obligatorias no detectadas para{" "}
                  {error.fdcType === "FDC_124" ? "F-DC-124 (Propuesta)" : "F-DC-125 (Informe Final)"}:
                </p>
                <ul className="mt-1.5 list-disc space-y-1 pl-5 text-xs text-slate-700">
                  {error.missingSections?.map((sectionKey) => (
                    <li key={sectionKey}>
                      <span className="font-semibold">{SECTION_LABELS[sectionKey] ?? sectionKey}</span>
                      {SECTION_LABELS[sectionKey] && (
                        <span className="text-slate-500"> ({sectionKey})</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {error.canRetry && onRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            leftIcon={<RotateCcw className="h-3.5 w-3.5" />}
            className="shrink-0 border-rose-300 text-rose-800 hover:bg-rose-100"
          >
            Reintentar análisis
          </Button>
        )}
      </div>
    </Card>
  );
}
