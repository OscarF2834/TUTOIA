import { useCallback, useEffect, useRef, useState } from "react";
import type { ActaExportFormat, DefenseSession, JuryProfile } from "@/domain/models/defense";
import type { FdcDocumentResult } from "@/domain/models/fdc";
import { mapDefenseApiError } from "@/domain/rules/defenseRules";
import { ApiHttpError } from "@/infrastructure/api/httpClient";
import { mergeTurnSubmissionIntoSession } from "@/infrastructure/api/mappers/defenseMapper";
import { tutoiaApi } from "@/infrastructure/api/TutoiaApiFacade";
import { triggerBrowserFileDownload } from "@/infrastructure/files/browserDownloadAdapter";
import { useDefenseAudio } from "@/presentation/hooks/useDefenseAudio";

const DEFENSE_SESSION_KEY = "tutoia.defense.lastSessionId";
const LAST_FDC_KEY = "tutoia.fdc.lastDocumentId";

function extractErrorMessage(err: unknown): string {
  if (err instanceof ApiHttpError) return mapDefenseApiError(err.status, err.detail, err.code);
  return err instanceof Error ? err.message : "Ocurrió un error inesperado en la sala AURA.";
}

export interface InitialDefenseParams {
  fdcDocumentId?: string | null;
  juryProfile?: JuryProfile | null;
}

export function useDefenseSession(initialParams: InitialDefenseParams = {}) {
  const [session, setSession] = useState<DefenseSession | null>(null);
  const [fdcDocument, setFdcDocument] = useState<FdcDocumentResult | null>(null);
  const [isHydrating, setIsHydrating] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isSubmittingTurn, setIsSubmittingTurn] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<ActaExportFormat | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mountedRef = useRef(true);
  const sessionRef = useRef<DefenseSession | null>(null);
  const audioRef = useRef<ReturnType<typeof useDefenseAudio> | null>(null);
  const submitTurnRef = useRef<
    (sessionId: string, fn: () => Promise<Awaited<ReturnType<typeof tutoiaApi.submitTextTurn>>>) => Promise<boolean>
  >(async () => false);

  const syncSession = useCallback(
    (updater: DefenseSession | null | ((prev: DefenseSession | null) => DefenseSession | null)) => {
      const next = typeof updater === "function" ? updater(sessionRef.current) : updater;
      sessionRef.current = next;
      setSession(next);
      return next;
    },
    [],
  );

  const audio = useDefenseAudio({
    onAudioReady: (sessionId, blob, filename) => {
      void submitTurnRef.current(sessionId, () =>
        tutoiaApi.submitAudioTurn(sessionId, blob, filename),
      );
    },
    onAudioError: (msg) => setErrorMessage(msg),
    onSpeechFinished: (targetSession) => {
      if (targetSession.state === "AURA_SPEAKING") {
        syncSession((prev) =>
          prev && prev.sessionId === targetSession.sessionId
            ? { ...prev, state: "LISTENING_STUDENT" }
            : prev,
        );
      }
    },
  });
  audioRef.current = audio;

  const applyTurnSubmission = useCallback(
    async (
      _sessionId: string,
      requestFn: () => Promise<Awaited<ReturnType<typeof tutoiaApi.submitTextTurn>>>,
    ): Promise<boolean> => {
      setIsSubmittingTurn(true);
      setErrorMessage(null);
      syncSession((prev) => (prev ? { ...prev, state: "EVALUATING_TURN" } : prev));
      try {
        const result = await requestFn();
        if (!mountedRef.current) return true;
        const currentSession = sessionRef.current;
        const updated = currentSession
          ? syncSession(mergeTurnSubmissionIntoSession(currentSession, result))
          : null;
        setIsSubmittingTurn(false);
        if (updated) {
          void audioRef.current?.speakPrompt(updated, !result.isCompleted, false);
        }
        return true;
      } catch (err) {
        if (!mountedRef.current) return false;
        setIsSubmittingTurn(false);
        syncSession((prev) => (prev ? { ...prev, state: "LISTENING_STUDENT" } : prev));
        setErrorMessage(extractErrorMessage(err));
        return false;
      }
    },
    [syncSession],
  );
  submitTurnRef.current = applyTurnSubmission;

  const loadFdcMetadata = useCallback(async (fdcDocumentId: string) => {
    try {
      const doc = await tutoiaApi.getFdcById(fdcDocumentId);
      if (mountedRef.current) setFdcDocument(doc);
    } catch {
      // Metadatos auxiliares opcionales
    }
  }, []);

  const startSession = useCallback(
    async (fdcDocumentId: string, juryProfile: JuryProfile) => {
      audioRef.current?.unlockAudio();
      audioRef.current?.stopAll();
      setIsCreating(true);
      setErrorMessage(null);
      try {
        const created = await tutoiaApi.createSession({ fdcDocumentId, juryProfile });
        if (!mountedRef.current) return;
        window.sessionStorage.setItem(DEFENSE_SESSION_KEY, created.sessionId);
        window.sessionStorage.setItem(LAST_FDC_KEY, created.fdcDocumentId);
        syncSession(created);
        setIsCreating(false);
        void loadFdcMetadata(created.fdcDocumentId);
        void audioRef.current?.speakPrompt(created, true, false);
      } catch (err) {
        if (!mountedRef.current) return;
        setIsCreating(false);
        setErrorMessage(extractErrorMessage(err));
      }
    },
    [loadFdcMetadata, syncSession],
  );

  useEffect(() => {
    mountedRef.current = true;
    const requestedFdc = initialParams.fdcDocumentId?.trim();
    if (requestedFdc) {
      window.history.replaceState(null, "", "#/defense");
      void startSession(requestedFdc, initialParams.juryProfile ?? "ESTANDAR_UTS");
    } else {
      const savedSessionId = window.sessionStorage.getItem(DEFENSE_SESSION_KEY);
      if (savedSessionId) {
        setIsHydrating(true);
        tutoiaApi
          .getSession(savedSessionId)
          .then((loaded) => {
            if (!mountedRef.current) return;
            syncSession(loaded);
            setIsHydrating(false);
            void loadFdcMetadata(loaded.fdcDocumentId);
            if (loaded.state !== "COMPLETED") {
              void audioRef.current?.speakPrompt(loaded, false, false);
            }
          })
          .catch(() => {
            if (!mountedRef.current) return;
            window.sessionStorage.removeItem(DEFENSE_SESSION_KEY);
            setIsHydrating(false);
          });
      } else {
        const lastFdcId = window.sessionStorage.getItem(LAST_FDC_KEY);
        if (lastFdcId) void loadFdcMetadata(lastFdcId);
      }
    }
    return () => {
      mountedRef.current = false;
    };
  }, [initialParams.fdcDocumentId, initialParams.juryProfile, loadFdcMetadata, startSession, syncSession]);

  const submitTextTurn = useCallback(
    async (text: string): Promise<boolean> => {
      const active = sessionRef.current;
      if (!active) return false;
      audio.unlockAudio();
      audio.stopAll();
      return applyTurnSubmission(active.sessionId, () =>
        tutoiaApi.submitTextTurn(active.sessionId, text),
      );
    },
    [applyTurnSubmission, audio],
  );

  const resetDefenseSession = useCallback(() => {
    audio.stopAll();
    window.sessionStorage.removeItem(DEFENSE_SESSION_KEY);
    syncSession(null);
    setExportError(null);
    setErrorMessage(null);
    const lastFdcId = window.sessionStorage.getItem(LAST_FDC_KEY);
    if (lastFdcId) void loadFdcMetadata(lastFdcId);
  }, [audio, loadFdcMetadata, syncSession]);

  const exportActa = useCallback(async (format: ActaExportFormat) => {
    const active = sessionRef.current;
    if (!active) return;
    setExportingFormat(format);
    setExportError(null);
    try {
      const file = await tutoiaApi.downloadActaReport(active.sessionId, format);
      triggerBrowserFileDownload(file.blob, file.filename);
    } catch (err) {
      if (mountedRef.current) setExportError(extractErrorMessage(err));
    } finally {
      if (mountedRef.current) setExportingFormat(null);
    }
  }, []);

  return {
    session,
    fdcDocument,
    isHydrating,
    isCreating,
    isSubmittingTurn,
    exportingFormat,
    exportError,
    isAuraSpeaking: audio.isAuraSpeaking,
    needsPlayGesture: audio.needsPlayGesture,
    isRecording: audio.isRecording,
    autoSubmitOnSilence: audio.autoSubmitOnSilence,
    audioLevel: audio.telemetry.audioLevel,
    frequencyBins: audio.telemetry.frequencyBins,
    elapsedSeconds: audio.telemetry.elapsedSeconds,
    hasSpoken: audio.telemetry.hasSpoken,
    silenceCountdownMs: audio.telemetry.silenceCountdownMs,
    errorMessage,
    startSession,
    exportActa,
    repeatQuestion: () => {
      const active = sessionRef.current;
      if (!active) return;
      audio.unlockAudio();
      void audio.speakPrompt(active, active.state !== "COMPLETED", true);
    },
    startMic: () => {
      const active = sessionRef.current;
      if (active) {
        setErrorMessage(null);
        audio.startMic(active.sessionId);
      }
    },
    stopAndSubmitMic: audio.stopAndSubmitMic,
    restartMic: audio.restartMic,
    toggleAutoSubmit: audio.toggleAutoSubmit,
    submitTextTurn,
    resetDefenseSession,
  };
}
