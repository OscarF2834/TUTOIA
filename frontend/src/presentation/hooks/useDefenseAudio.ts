import { useCallback, useEffect, useRef, useState } from "react";
import type { DefenseSession } from "@/domain/models/defense";
import { tutoiaApi } from "@/infrastructure/api/TutoiaApiFacade";
import { AuraAudioPlayerAdapter } from "@/infrastructure/audio/AuraAudioPlayerAdapter";
import {
  InteractiveMicRecorderAdapter,
  type MicTelemetryFrame,
} from "@/infrastructure/audio/InteractiveMicRecorderAdapter";

export const IDLE_DEFENSE_TELEMETRY: MicTelemetryFrame = {
  audioLevel: 0,
  frequencyBins: new Array<number>(28).fill(0),
  elapsedSeconds: 0,
  hasSpoken: false,
  silenceCountdownMs: null,
};

export interface UseDefenseAudioOptions {
  onAudioReady: (sessionId: string, blob: Blob, filename: string) => void;
  onAudioError: (message: string) => void;
  onSpeechFinished?: (session: DefenseSession) => void;
}

export function useDefenseAudio({
  onAudioReady,
  onAudioError,
  onSpeechFinished,
}: UseDefenseAudioOptions) {
  const [isAuraSpeaking, setIsAuraSpeaking] = useState(false);
  const [needsPlayGesture, setNeedsPlayGesture] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [autoSubmitOnSilence, setAutoSubmitOnSilence] = useState(true);
  const [telemetry, setTelemetry] = useState<MicTelemetryFrame>(IDLE_DEFENSE_TELEMETRY);

  const playerRef = useRef<AuraAudioPlayerAdapter | null>(null);
  const recorderRef = useRef<InteractiveMicRecorderAdapter | null>(null);
  const mountedRef = useRef(true);
  const speakRunRef = useRef(0);
  const autoSubmitRef = useRef(true);
  const callbacksRef = useRef({ onAudioReady, onAudioError, onSpeechFinished });

  if (!playerRef.current) playerRef.current = new AuraAudioPlayerAdapter();
  if (!recorderRef.current) recorderRef.current = new InteractiveMicRecorderAdapter();
  autoSubmitRef.current = autoSubmitOnSilence;
  callbacksRef.current = { onAudioReady, onAudioError, onSpeechFinished };

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      playerRef.current?.dispose();
      recorderRef.current?.dispose();
    };
  }, []);

  const startMic = useCallback(async (sessionId: string) => {
    const recorder = recorderRef.current;
    if (!recorder || !mountedRef.current) return;
    await recorder.start(
      {
        onFrame: (frame) => {
          if (mountedRef.current) setTelemetry(frame);
        },
        onAudioReady: (blob, filename) => {
          if (!mountedRef.current) return;
          setIsRecording(false);
          callbacksRef.current.onAudioReady(sessionId, blob, filename);
        },
        onError: (msg) => {
          if (!mountedRef.current) return;
          setIsRecording(false);
          callbacksRef.current.onAudioError(msg);
        },
      },
      autoSubmitRef.current,
    );
    if (mountedRef.current && recorder.isRecording) setIsRecording(true);
  }, []);

  const speakPrompt = useCallback(
    async (targetSession: DefenseSession, autoListenAfter: boolean) => {
      const player = playerRef.current;
      const recorder = recorderRef.current;
      if (!player || !recorder) return;

      recorder.cancel();
      setIsRecording(false);
      const runId = ++speakRunRef.current;
      setIsAuraSpeaking(true);
      setNeedsPlayGesture(false);

      const promptText = targetSession.activeQuestionText;
      const outcome = await player.playPrompt(
        () => tutoiaApi.synthesizeSpeech(targetSession.sessionId, promptText),
        promptText,
        (audioLevel, frequencyBins) => {
          if (!mountedRef.current || runId !== speakRunRef.current) return;
          setTelemetry({ ...IDLE_DEFENSE_TELEMETRY, audioLevel, frequencyBins });
        },
      );

      if (!mountedRef.current || runId !== speakRunRef.current) return;
      setIsAuraSpeaking(false);
      if (outcome === "blocked") {
        setNeedsPlayGesture(true);
        return;
      }

      callbacksRef.current.onSpeechFinished?.(targetSession);
      if (autoListenAfter && targetSession.state !== "COMPLETED") {
        await startMic(targetSession.sessionId);
      }
    },
    [startMic],
  );

  const stopAll = useCallback(() => {
    recorderRef.current?.cancel();
    playerRef.current?.stop();
    setIsRecording(false);
    setIsAuraSpeaking(false);
    setNeedsPlayGesture(false);
    setTelemetry(IDLE_DEFENSE_TELEMETRY);
  }, []);

  const toggleAutoSubmit = useCallback(() => {
    setAutoSubmitOnSilence((prev) => {
      const next = !prev;
      recorderRef.current?.setAutoSubmitOnSilence(next);
      setTelemetry((cur) => ({ ...cur, silenceCountdownMs: null }));
      return next;
    });
  }, []);

  return {
    isAuraSpeaking,
    needsPlayGesture,
    isRecording,
    autoSubmitOnSilence,
    telemetry,
    unlockAudio: () => void playerRef.current?.unlock(),
    stopAll,
    speakPrompt,
    startMic: (sessionId: string) => {
      void playerRef.current?.unlock();
      playerRef.current?.stop();
      setIsAuraSpeaking(false);
      void startMic(sessionId);
    },
    stopAndSubmitMic: () => recorderRef.current?.finishAndSubmit(),
    restartMic: () => recorderRef.current?.restart(),
    toggleAutoSubmit,
  };
}
