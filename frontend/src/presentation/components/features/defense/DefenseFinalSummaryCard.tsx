import { Award, CheckCircle2, FileDown, RotateCcw, Sparkles, TrendingUp, Volume2 } from "lucide-react";
import type { DefenseSession } from "@/domain/models/defense";
import { CRITERION_META, JURY_PROFILE_LABELS, VERDICT_META } from "@/domain/rules/defenseRules";
import { Badge, Button, Card, ProgressBar } from "@/presentation/components/ui";

export interface DefenseFinalSummaryCardProps {
  session: DefenseSession;
  isAuraSpeaking: boolean;
  onReplayClosing: () => void;
  onStartNewDefense: () => void;
}

export function DefenseFinalSummaryCard({
  session,
  isAuraSpeaking,
  onReplayClosing,
  onStartNewDefense,
}: DefenseFinalSummaryCardProps) {
  const summary = session.finalSummary;
  if (!summary || session.overallScore === null) return null;

  const verdictMeta = VERDICT_META[summary.verdict];

  return (
    <Card
      title="Resultado consolidado de sustentación"
      subtitle={`Perfil aplicado: ${JURY_PROFILE_LABELS[session.juryProfile]} · ${session.turns.length} intervenciones`}
      headerAction={
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={verdictMeta.badgeVariant} dot>
            {verdictMeta.label}
          </Badge>
          <Badge variant="brand">
            <span className="tabular-nums">{session.overallScore.toFixed(2)} / 5.0</span>
          </Badge>
        </div>
      }
      footer={
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Button
            type="button"
            variant="outline"
            size="md"
            disabled
            title="La generación oficial de acta PDF institucional estará disponible en el Módulo 3."
            leftIcon={<FileDown className="h-4 w-4" />}
          >
            Exportar acta PDF (Módulo 3 · Próximamente)
          </Button>
          <Button
            type="button"
            variant="primary"
            size="md"
            onClick={onStartNewDefense}
            leftIcon={<RotateCcw className="h-4 w-4" />}
          >
            Iniciar nueva sustentación
          </Button>
        </div>
      }
    >
      <div className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50/70 p-4">
          <div className="space-y-1">
            <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-emerald-900">
              <Award className="h-4 w-4 text-emerald-700" aria-hidden="true" />
              Mensaje de cierre de AURA
            </p>
            <p className="text-sm leading-relaxed text-slate-800">{summary.closingMessage}</p>
          </div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={isAuraSpeaking}
            onClick={onReplayClosing}
            leftIcon={<Volume2 className="h-3.5 w-3.5" />}
          >
            Escuchar cierre
          </Button>
        </div>

        <section className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-900">
            Desglose por criterios de rúbrica UTS
          </h3>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {CRITERION_META.map((criterion) => {
              const score = summary.criteriaAverages[criterion.code] ?? 0;
              return (
                <div
                  key={criterion.code}
                  className="rounded-lg border border-slate-200 bg-slate-50/70 p-3"
                >
                  <div className="mb-1.5 flex items-center justify-between gap-2 text-xs">
                    <span className="font-semibold text-slate-800">
                      {criterion.label}{" "}
                      <span className="font-normal text-slate-500">({criterion.weightPercent}%)</span>
                    </span>
                    <span className="font-semibold text-slate-900 tabular-nums">
                      {score.toFixed(2)} / 5.0
                    </span>
                  </div>
                  <ProgressBar value={(score / 5) * 100} tone="brand" />
                </div>
              );
            })}
          </div>
        </section>

        <div className="grid grid-cols-1 gap-4 border-t border-slate-200 pt-4 sm:grid-cols-2">
          <section className="space-y-2">
            <h3 className="flex items-center gap-1.5 text-sm font-semibold text-slate-900">
              <CheckCircle2 className="h-4 w-4 text-emerald-700" aria-hidden="true" />
              Fortalezas observadas
            </h3>
            <ul className="list-disc space-y-1.5 pl-5 text-xs leading-relaxed text-slate-700">
              {summary.strengths.map((item, idx) => (
                <li key={`str-${idx}`}>{item}</li>
              ))}
            </ul>
          </section>

          <section className="space-y-2">
            <h3 className="flex items-center gap-1.5 text-sm font-semibold text-slate-900">
              <TrendingUp className="h-4 w-4 text-sky-700" aria-hidden="true" />
              Oportunidades de mejora
            </h3>
            <ul className="list-disc space-y-1.5 pl-5 text-xs leading-relaxed text-slate-700">
              {summary.improvements.map((item, idx) => (
                <li key={`imp-${idx}`}>{item}</li>
              ))}
            </ul>
          </section>
        </div>

        <div className="flex items-start gap-2.5 rounded-lg border border-slate-200 bg-slate-100 px-4 py-3 text-xs leading-relaxed text-slate-600">
          <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" aria-hidden="true" />
          <p>
            <strong className="text-slate-800">Supervisión humana (Human-in-the-Loop): </strong>
            {summary.humanInTheLoopNotice}
          </p>
        </div>
      </div>
    </Card>
  );
}
