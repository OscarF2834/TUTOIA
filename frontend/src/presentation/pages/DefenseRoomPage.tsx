import { useState } from "react";
import { AlertCircle, ArrowLeft, Bot, GraduationCap, Play } from "lucide-react";
import type { DefenseState, JuryProfile } from "@/domain/models/defense";
import {
  DEFENSE_STATE_LABELS,
  JURY_PROFILE_LABELS,
  JURY_PROFILE_OPTIONS,
} from "@/domain/rules/defenseRules";
import { FDC_TYPE_LABELS, getGapAxisLabel } from "@/domain/rules/fdcFileRules";
import { AuraJarvisCore } from "@/presentation/components/features/defense/AuraJarvisCore";
import { DefenseControlsBar } from "@/presentation/components/features/defense/DefenseControlsBar";
import { DefenseFinalSummaryCard } from "@/presentation/components/features/defense/DefenseFinalSummaryCard";
import { DefenseTranscriptPanel } from "@/presentation/components/features/defense/DefenseTranscriptPanel";
import { Badge, Button, Card, Select } from "@/presentation/components/ui";
import {
  useDefenseSession,
  type InitialDefenseParams,
} from "@/presentation/hooks/useDefenseSession";

export interface DefenseRoomPageProps {
  initialParams?: InitialDefenseParams;
  onBackToFdc: () => void;
}

export default function DefenseRoomPage({ initialParams, onBackToFdc }: DefenseRoomPageProps) {
  const {
    session,
    fdcDocument,
    isHydrating,
    isCreating,
    isSubmittingTurn,
    exportingFormat,
    exportError,
    isAuraSpeaking,
    needsPlayGesture,
    isRecording,
    autoSubmitOnSilence,
    audioLevel,
    frequencyBins,
    elapsedSeconds,
    hasSpoken,
    silenceCountdownMs,
    errorMessage,
    startSession,
    exportActa,
    repeatQuestion,
    startMic,
    stopAndSubmitMic,
    restartMic,
    toggleAutoSubmit,
    submitTextTurn,
    resetDefenseSession,
  } = useDefenseSession(initialParams);

  const [selectedJury, setSelectedJury] = useState<JuryProfile>("ESTANDAR_UTS");

  const visualState: DefenseState = isSubmittingTurn
    ? "EVALUATING_TURN"
    : isAuraSpeaking
      ? "AURA_SPEAKING"
      : isRecording
        ? "LISTENING_STUDENT"
        : (session?.state ?? "PREPARING");

  const currentQuestion = session?.plannedQuestions[session.currentQuestionIndex];
  const fdcType = fdcDocument?.fdcType ?? "FDC_125";
  const currentAxisLabel = currentQuestion
    ? getGapAxisLabel(currentQuestion.thematicAxis, fdcType)
    : "Sustentación oral";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-6xl px-4 py-7 sm:px-6">
        <header className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
          <div className="flex items-center gap-3.5">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-700 text-white shadow-sm">
              <GraduationCap className="h-6 w-6" aria-hidden="true" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl font-semibold tracking-tight text-slate-900">
                  Sala de Sustentación Oral · AURA
                </h1>
                <Badge variant="brand" size="sm">
                  UTS · Módulo 2
                </Badge>
                {session && (
                  <Badge variant="info" size="sm">
                    {JURY_PROFILE_LABELS[session.juryProfile]}
                  </Badge>
                )}
              </div>
              <p className="text-sm text-slate-600">
                {fdcDocument
                  ? `${fdcDocument.project.title} (${FDC_TYPE_LABELS[fdcDocument.fdcType]})`
                  : "Simulación evaluativa con Gemini Dialog, Gemini TTS y Gemini Transcribe."}
              </p>
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onBackToFdc}
            leftIcon={<ArrowLeft className="h-4 w-4" />}
          >
            Volver al Módulo 1
          </Button>
        </header>

        {errorMessage && (
          <div
            role="alert"
            className="mb-5 flex items-start gap-2.5 rounded-xl border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-900"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-700" aria-hidden="true" />
            <span>{errorMessage}</span>
          </div>
        )}

        {(isHydrating || isCreating) && (
          <Card title="Preparando sala con AURA">
            <p className="text-sm text-slate-600">
              {isCreating
                ? "Generando preguntas contextualizadas al documento FDC y configurando voz de AURA…"
                : "Recuperando el estado de tu última sustentación guardada en esta sesión…"}
            </p>
          </Card>
        )}

        {!isHydrating && !isCreating && !session && (
          <Card
            title="No hay una sustentación activa en curso"
            subtitle="Inicia una nueva sesión desde el último documento FDC analizado o regresa al Módulo 1 para cargar uno."
          >
            {fdcDocument ? (
              <div className="space-y-4">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm">
                  <p className="font-semibold text-slate-900">{fdcDocument.project.title}</p>
                  <p className="mt-1 text-xs text-slate-600">
                    {FDC_TYPE_LABELS[fdcDocument.fdcType]} · {fdcDocument.originalFilename}
                  </p>
                </div>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                  <div className="sm:w-72">
                    <Select
                      label="Perfil de jurado evaluador"
                      value={selectedJury}
                      options={JURY_PROFILE_OPTIONS}
                      onChange={(e) => setSelectedJury(e.target.value as JuryProfile)}
                    />
                  </div>
                  <Button
                    type="button"
                    variant="primary"
                    size="md"
                    onClick={() => void startSession(fdcDocument.documentId, selectedJury)}
                    leftIcon={<Play className="h-4 w-4" />}
                  >
                    Iniciar sustentación con AURA
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex flex-wrap items-center justify-between gap-4">
                <p className="text-sm text-slate-600">
                  Primero analiza una propuesta F-DC-124 o informe F-DC-125 en el Módulo 1.
                </p>
                <Button type="button" variant="primary" size="md" onClick={onBackToFdc}>
                  Ir al Módulo 1 · Análisis FDC
                </Button>
              </div>
            )}
          </Card>
        )}

        {!isHydrating && !isCreating && session && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            <div className="space-y-5 lg:col-span-5">
              <AuraJarvisCore
                state={visualState}
                audioLevel={audioLevel}
                frequencyBins={frequencyBins}
                statusLabel={DEFENSE_STATE_LABELS[visualState]}
                subLabel={
                  session.state === "COMPLETED"
                    ? "Evaluación consolidada lista"
                    : `Eje actual: ${currentAxisLabel}`
                }
              />

              <Card
                title={
                  session.state === "COMPLETED"
                    ? "Cierre de AURA"
                    : `Pregunta activa · ${currentAxisLabel}`
                }
                subtitle={
                  session.state !== "COMPLETED" && currentQuestion?.sourceSection
                    ? `Referencia documental: ${currentQuestion.sourceSection}`
                    : undefined
                }
                headerAction={
                  session.isFollowUpPending ? (
                    <Badge variant="warning" size="sm">
                      Contrapregunta
                    </Badge>
                  ) : (
                    <Badge variant="info" size="sm">
                      AURA
                    </Badge>
                  )
                }
              >
                <div className="flex items-start gap-2.5 text-sm leading-relaxed text-slate-800">
                  <Bot className="mt-1 h-4 w-4 shrink-0 text-sky-700" aria-hidden="true" />
                  <p>{session.activeQuestionText}</p>
                </div>
              </Card>

              {session.state !== "COMPLETED" && (
                <DefenseControlsBar
                  state={visualState}
                  currentQuestionIndex={session.currentQuestionIndex}
                  totalQuestions={session.totalQuestions}
                  isFollowUpPending={session.isFollowUpPending}
                  isRecording={isRecording}
                  isSubmitting={isSubmittingTurn}
                  isAuraSpeaking={isAuraSpeaking}
                  needsPlayGesture={needsPlayGesture}
                  elapsedSeconds={elapsedSeconds}
                  hasSpoken={hasSpoken}
                  silenceCountdownMs={silenceCountdownMs}
                  autoSubmitOnSilence={autoSubmitOnSilence}
                  onStartMic={startMic}
                  onStopAndSubmitMic={stopAndSubmitMic}
                  onRestartMic={restartMic}
                  onToggleAutoSubmit={toggleAutoSubmit}
                  onRepeatQuestion={repeatQuestion}
                  onSubmitText={submitTextTurn}
                />
              )}
            </div>

            <div className="space-y-5 lg:col-span-7">
              {session.state === "COMPLETED" && (
                <DefenseFinalSummaryCard
                  session={session}
                  isAuraSpeaking={isAuraSpeaking}
                  exportingFormat={exportingFormat}
                  exportError={exportError}
                  onExportActa={(format) => void exportActa(format)}
                  onReplayClosing={repeatQuestion}
                  onStartNewDefense={resetDefenseSession}
                />
              )}

              <DefenseTranscriptPanel
                turns={session.turns}
                state={visualState}
                fdcType={fdcType}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
