import { useState, type FormEvent } from "react";
import {
  Keyboard,
  Mic,
  PauseCircle,
  PlayCircle,
  RotateCcw,
  Send,
  Volume2,
} from "lucide-react";
import type { DefenseState } from "@/domain/models/defense";
import { formatTurnClock, validateTextTurn } from "@/domain/rules/defenseRules";
import { Badge, Button, Card, Textarea } from "@/presentation/components/ui";

export interface DefenseControlsBarProps {
  state: DefenseState;
  currentQuestionIndex: number;
  totalQuestions: number;
  isFollowUpPending: boolean;
  isRecording: boolean;
  isSubmitting: boolean;
  isAuraSpeaking: boolean;
  needsPlayGesture: boolean;
  elapsedSeconds: number;
  hasSpoken: boolean;
  silenceCountdownMs: number | null;
  autoSubmitOnSilence: boolean;
  onStartMic: () => void;
  onStopAndSubmitMic: () => void;
  onRestartMic: () => void;
  onToggleAutoSubmit: () => void;
  onRepeatQuestion: () => void;
  onSubmitText: (text: string) => Promise<boolean>;
}

export function DefenseControlsBar({
  state,
  currentQuestionIndex,
  totalQuestions,
  isFollowUpPending,
  isRecording,
  isSubmitting,
  isAuraSpeaking,
  needsPlayGesture,
  elapsedSeconds,
  hasSpoken,
  silenceCountdownMs,
  autoSubmitOnSilence,
  onStartMic,
  onStopAndSubmitMic,
  onRestartMic,
  onToggleAutoSubmit,
  onRepeatQuestion,
  onSubmitText,
}: DefenseControlsBarProps) {
  const [textModeOpen, setTextModeOpen] = useState(false);
  const [draftText, setDraftText] = useState("");
  const [textError, setTextError] = useState<string | null>(null);

  const isBusy = isSubmitting || state === "EVALUATING_TURN" || state === "PREPARING";
  const canInteract = state !== "COMPLETED" && !isBusy;

  const handleTextSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const validationError = validateTextTurn(draftText);
    if (validationError) {
      setTextError(validationError);
      return;
    }
    setTextError(null);
    const accepted = await onSubmitText(draftText.trim());
    if (accepted) {
      setDraftText("");
      setTextModeOpen(false);
    }
  };

  const silenceSeconds =
    silenceCountdownMs !== null ? (silenceCountdownMs / 1000).toFixed(1) : null;

  return (
    <Card padding="md">
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="brand" size="sm">
              Pregunta {Math.min(currentQuestionIndex + 1, totalQuestions)} de {totalQuestions}
            </Badge>
            {isFollowUpPending && (
              <Badge variant="warning" size="sm" dot>
                Contrapregunta
              </Badge>
            )}
          </div>
          <span className="text-xs font-semibold text-slate-600 tabular-nums">
            Turno: {formatTurnClock(elapsedSeconds)}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {!isRecording ? (
            <Button
              type="button"
              variant="primary"
              size="md"
              disabled={!canInteract || isAuraSpeaking}
              isLoading={isBusy}
              onClick={onStartMic}
              leftIcon={<Mic className="h-4 w-4" />}
            >
              {isBusy ? "Evaluando intervención…" : "Responder con micrófono"}
            </Button>
          ) : (
            <>
              <Button
                type="button"
                variant="primary"
                size="md"
                onClick={onStopAndSubmitMic}
                leftIcon={<Send className="h-4 w-4" />}
              >
                Terminar y enviar respuesta
              </Button>
              <Button
                type="button"
                variant="outline"
                size="md"
                onClick={onRestartMic}
                leftIcon={<RotateCcw className="h-4 w-4" />}
              >
                Regrabar
              </Button>
            </>
          )}

          <Button
            type="button"
            variant={needsPlayGesture ? "primary" : "secondary"}
            size="md"
            disabled={isBusy}
            onClick={onRepeatQuestion}
            leftIcon={<Volume2 className="h-4 w-4" />}
          >
            {needsPlayGesture ? "Escuchar pregunta ahora" : "Repetir pregunta"}
          </Button>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              aria-pressed={autoSubmitOnSilence}
              onClick={onToggleAutoSubmit}
              leftIcon={
                autoSubmitOnSilence ? (
                  <PauseCircle className="h-3.5 w-3.5 text-emerald-700" />
                ) : (
                  <PlayCircle className="h-3.5 w-3.5 text-slate-500" />
                )
              }
            >
              Envío automático tras 10s de silencio: {autoSubmitOnSilence ? "Activo" : "Manual"}
            </Button>
          </div>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={!canInteract}
            onClick={() => setTextModeOpen((prev) => !prev)}
            leftIcon={<Keyboard className="h-3.5 w-3.5" />}
          >
            {textModeOpen ? "Ocultar respuesta escrita" : "Responder por texto"}
          </Button>
        </div>

        {isRecording && (
          <p aria-live="polite" className="text-xs font-medium text-emerald-800">
            {silenceSeconds !== null
              ? `Pausa detectada: finalizando en ${silenceSeconds} s… sigue hablando o pulsa «Terminar y enviar respuesta».`
              : hasSpoken
                ? autoSubmitOnSilence
                  ? "Voz detectada. Al finalizar tu idea (10 s de silencio) se enviará automáticamente."
                  : "Grabando en modo manual. Pulsa «Terminar y enviar respuesta» cuando concluyas."
                : "Micrófono abierto. Habla con claridad para iniciar tu respuesta."}
          </p>
        )}

        {textModeOpen && (
          <form onSubmit={handleTextSubmit} className="space-y-3 border-t border-slate-200 pt-3">
            <Textarea
              label="Respuesta escrita de respaldo"
              placeholder="Escriba aquí su sustentación si no dispone de micrófono o prefiere responder por texto…"
              value={draftText}
              onChange={(e) => {
                setDraftText(e.target.value);
                if (textError) setTextError(null);
              }}
              error={textError ?? undefined}
              disabled={!canInteract}
              rows={3}
            />
            <div className="flex justify-end">
              <Button
                type="submit"
                variant="secondary"
                size="sm"
                disabled={!canInteract}
                isLoading={isBusy}
                leftIcon={<Send className="h-3.5 w-3.5" />}
              >
                Enviar respuesta escrita
              </Button>
            </div>
          </form>
        )}
      </div>
    </Card>
  );
}
