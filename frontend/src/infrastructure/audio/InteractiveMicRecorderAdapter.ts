import { normalizeRecordedAudioForBackend } from "@/infrastructure/audio/wavEncoder";

export interface MicTelemetryFrame {
  audioLevel: number;
  frequencyBins: number[];
  elapsedSeconds: number;
  hasSpoken: boolean;
  silenceCountdownMs: number | null;
}

export interface MicRecorderCallbacks {
  onFrame: (frame: MicTelemetryFrame) => void;
  onAudioReady: (blob: Blob, filename: string) => void;
  onError: (message: string) => void;
}

const BIN_COUNT = 28;
const SPEECH_RMS_THRESHOLD = 0.02;
const MIN_ACTIVE_SPEECH_MS = 1200;
const AUTO_SUBMIT_SILENCE_MS = 10_000;
const SILENCE_COUNTDOWN_SHOW_MS = 1000;
const MIME_CANDIDATES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/ogg",
  "audio/mp4",
];

function selectSupportedMimeType(): string {
  if (typeof MediaRecorder === "undefined") return "";
  for (const candidate of MIME_CANDIDATES) {
    if (MediaRecorder.isTypeSupported(candidate)) {
      return candidate;
    }
  }
  return "";
}

export class InteractiveMicRecorderAdapter {
  private stream: MediaStream | null = null;
  private recorder: MediaRecorder | null = null;
  private audioCtx: AudioContext | null = null;
  private rafId: number | null = null;
  private chunks: Blob[] = [];
  private callbacks: MicRecorderCallbacks | null = null;
  private stopIntent: "submit" | "restart" | "cancel" = "cancel";
  private autoSubmitOnSilence = true;
  private activeSpeechMs = 0;
  private silenceMs = 0;
  private startedAtMs = 0;
  private lastTickMs = 0;
  private activeMimeType = "audio/webm";

  get isRecording(): boolean {
    return this.recorder?.state === "recording";
  }

  setAutoSubmitOnSilence(enabled: boolean): void {
    this.autoSubmitOnSilence = enabled;
    this.silenceMs = 0;
  }

  async start(callbacks: MicRecorderCallbacks, autoSubmitOnSilence: boolean): Promise<void> {
    this.cancel();
    this.callbacks = callbacks;
    this.autoSubmitOnSilence = autoSubmitOnSilence;

    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      callbacks.onError("Tu navegador no soporta grabación de micrófono; usa el envío por texto.");
      return;
    }

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
    } catch {
      callbacks.onError("Permiso de micrófono denegado o dispositivo no disponible.");
      return;
    }

    this.launchRecorder();
  }

  finishAndSubmit(): void {
    if (this.recorder && this.recorder.state === "recording") {
      this.stopIntent = "submit";
      this.recorder.stop();
    }
  }

  restart(): void {
    if (this.recorder && this.recorder.state === "recording") {
      this.stopIntent = "restart";
      this.recorder.stop();
      return;
    }
    if (this.stream && this.callbacks) {
      this.launchRecorder();
    }
  }

  cancel(): void {
    this.stopIntent = "cancel";
    this.stopMonitoring();
    if (this.recorder && this.recorder.state === "recording") {
      try {
        this.recorder.stop();
      } catch {
        // Grabadora ya detenida
      }
    }
    this.recorder = null;
    this.releaseStream();
  }

  dispose(): void {
    this.cancel();
    this.callbacks = null;
  }

  private launchRecorder(): void {
    if (!this.stream) return;
    this.chunks = [];
    this.activeSpeechMs = 0;
    this.silenceMs = 0;
    this.startedAtMs = performance.now();
    this.lastTickMs = this.startedAtMs;

    const chosenMime = selectSupportedMimeType();
    const recorder = chosenMime
      ? new MediaRecorder(this.stream, { mimeType: chosenMime })
      : new MediaRecorder(this.stream);
    this.activeMimeType = recorder.mimeType || chosenMime || "audio/webm";
    this.recorder = recorder;

    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) this.chunks.push(event.data);
    };
    recorder.onstop = () => void this.handleRecorderStop();

    recorder.start(250);
    this.startMonitoring();
  }

  private async handleRecorderStop(): Promise<void> {
    this.stopMonitoring();
    const intent = this.stopIntent;
    const rawChunks = this.chunks;
    this.chunks = [];

    if (intent === "restart") {
      this.launchRecorder();
      return;
    }

    this.releaseStream();
    this.recorder = null;
    this.callbacks?.onFrame({
      audioLevel: 0,
      frequencyBins: new Array<number>(BIN_COUNT).fill(0),
      elapsedSeconds: 0,
      hasSpoken: false,
      silenceCountdownMs: null,
    });

    if (intent !== "submit") return;
    if (rawChunks.length === 0) {
      this.callbacks?.onError("No se capturó audio suficiente. Intente hablar nuevamente.");
      return;
    }

    try {
      const rawBlob = new Blob(rawChunks, { type: this.activeMimeType });
      const normalized = await normalizeRecordedAudioForBackend(rawBlob, this.activeMimeType);
      this.callbacks?.onAudioReady(normalized.blob, normalized.filename);
    } catch {
      this.callbacks?.onError("No fue posible procesar el audio grabado en este navegador.");
    }
  }

  private startMonitoring(): void {
    if (!this.stream) return;
    const AudioCtx =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ctx = new AudioCtx();
    this.audioCtx = ctx;

    const analyser = ctx.createAnalyser();
    analyser.fftSize = 128;
    analyser.smoothingTimeConstant = 0.72;
    const source = ctx.createMediaStreamSource(this.stream);
    source.connect(analyser);

    const timeData = new Uint8Array(analyser.fftSize);
    const freqData = new Uint8Array(analyser.frequencyBinCount);

    const tick = (now: number) => {
      if (!this.recorder || this.recorder.state !== "recording") return;
      const dt = Math.min(120, Math.max(0, now - this.lastTickMs));
      this.lastTickMs = now;

      analyser.getByteTimeDomainData(timeData);
      let sqSum = 0;
      for (let i = 0; i < timeData.length; i += 1) {
        const norm = (timeData[i] - 128) / 128;
        sqSum += norm * norm;
      }
      const rms = Math.sqrt(sqSum / timeData.length);

      if (rms >= SPEECH_RMS_THRESHOLD) {
        this.activeSpeechMs += dt;
        this.silenceMs = 0;
      } else if (this.activeSpeechMs >= MIN_ACTIVE_SPEECH_MS) {
        this.silenceMs += dt;
      }

      analyser.getByteFrequencyData(freqData);
      const bins = Array.from({ length: BIN_COUNT }, (_, idx) =>
        idx < freqData.length ? freqData[idx] / 255 : 0,
      );
      const hasSpoken = this.activeSpeechMs >= MIN_ACTIVE_SPEECH_MS;
      const countdown =
        this.autoSubmitOnSilence && hasSpoken && this.silenceMs >= SILENCE_COUNTDOWN_SHOW_MS
          ? Math.max(0, AUTO_SUBMIT_SILENCE_MS - this.silenceMs)
          : null;

      this.callbacks?.onFrame({
        audioLevel: Math.min(1, rms * 4.5),
        frequencyBins: bins,
        elapsedSeconds: Math.floor((now - this.startedAtMs) / 1000),
        hasSpoken,
        silenceCountdownMs: countdown,
      });

      if (this.autoSubmitOnSilence && hasSpoken && this.silenceMs >= AUTO_SUBMIT_SILENCE_MS) {
        this.finishAndSubmit();
        return;
      }
      this.rafId = window.requestAnimationFrame(tick);
    };

    this.rafId = window.requestAnimationFrame(tick);
  }

  private stopMonitoring(): void {
    if (this.rafId !== null) {
      window.cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    if (this.audioCtx) {
      void this.audioCtx.close().catch(() => {});
      this.audioCtx = null;
    }
  }

  private releaseStream(): void {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
  }
}
