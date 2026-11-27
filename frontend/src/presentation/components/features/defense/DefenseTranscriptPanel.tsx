import { Bot, Loader2, Mic, MessageSquareText, User } from "lucide-react";
import type { DefenseState, DefenseTurn } from "@/domain/models/defense";
import type { FdcType } from "@/domain/models/fdc";
import { getGapAxisLabel } from "@/domain/rules/fdcFileRules";
import { Badge, Card } from "@/presentation/components/ui";

export interface DefenseTranscriptPanelProps {
  turns: DefenseTurn[];
  state: DefenseState;
  fdcType?: FdcType;
}

function scoreBadgeVariant(score: number): "success" | "warning" | "danger" {
  if (score >= 3.5) return "success";
  if (score >= 3.0) return "warning";
  return "danger";
}

export function DefenseTranscriptPanel({
  turns,
  state,
  fdcType = "FDC_125",
}: DefenseTranscriptPanelProps) {
  return (
    <Card
      title="Bitácora de sustentación oral"
      subtitle="Registro cronológico de preguntas de AURA, transcripción fiel y evaluación por turno."
      headerAction={
        <Badge variant="neutral" size="sm">
          {turns.length} {turns.length === 1 ? "turno evaluado" : "turnos evaluados"}
        </Badge>
      }
    >
      <div className="space-y-4">
        {turns.length === 0 && state !== "EVALUATING_TURN" && (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/80 px-4 py-6 text-center text-sm text-slate-600">
            Escucha la primera pregunta de AURA e interviene por micrófono (o texto) para iniciar el
            registro evaluativo.
          </div>
        )}

        {turns.map((turn) => (
          <article
            key={turn.id}
            className="space-y-3 rounded-xl border border-slate-200 bg-slate-50/60 p-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="info" size="sm">
                  Turno {turn.turnNumber} · {getGapAxisLabel(turn.thematicAxis, fdcType)}
                </Badge>
                {turn.isFollowUp && (
                  <Badge variant="warning" size="sm">
                    Contrapregunta
                  </Badge>
                )}
              </div>
              <Badge variant={scoreBadgeVariant(turn.weightedScore)} size="sm">
                <span className="tabular-nums">{turn.weightedScore.toFixed(2)} / 5.0</span>
              </Badge>
            </div>

            <div className="flex items-start gap-2.5 text-xs leading-relaxed text-slate-800">
              <Bot className="mt-0.5 h-4 w-4 shrink-0 text-sky-700" aria-hidden="true" />
              <p>
                <span className="font-semibold text-slate-900">AURA: </span>
                {turn.auraQuestionText}
              </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white px-3.5 py-2.5">
              <div className="mb-1 flex items-center justify-between gap-2 text-[11px] font-medium text-slate-500">
                <span className="inline-flex items-center gap-1 text-emerald-800">
                  <User className="h-3.5 w-3.5" aria-hidden="true" />
                  Sustentante
                </span>
                <span className="inline-flex items-center gap-1">
                  {turn.inputMode === "AUDIO" ? (
                    <>
                      <Mic className="h-3 w-3" aria-hidden="true" />
                      Voz · Gemini Transcribe
                    </>
                  ) : (
                    <>
                      <MessageSquareText className="h-3 w-3" aria-hidden="true" />
                      Texto escrito
                    </>
                  )}
                </span>
              </div>
              <p className="text-sm leading-relaxed text-slate-700">{turn.studentTranscript}</p>
            </div>

            <div className="rounded-lg border border-sky-200 bg-sky-50/70 px-3.5 py-2 text-xs leading-relaxed text-sky-900">
              <span className="font-semibold">Retroalimentación del jurado IA: </span>
              {turn.turnFeedback}
            </div>
          </article>
        ))}

        {state === "EVALUATING_TURN" && (
          <div
            aria-live="polite"
            className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-100 px-4 py-3.5 text-sm text-slate-700"
          >
            <Loader2 className="h-4 w-4 shrink-0 animate-spin text-emerald-700" aria-hidden="true" />
            <span>
              Transcribiendo y evaluando tu intervención frente a la rúbrica institucional UTS…
            </span>
          </div>
        )}
      </div>
    </Card>
  );
}
