export type AudioPlaybackOutcome = "tts" | "web-speech" | "blocked";

export type AudioLevelListener = (audioLevel: number, frequencyBins: number[]) => void;

const BIN_COUNT = 28;
let sharedAudioContext: AudioContext | null = null;
let gestureListenerAttached = false;

function getAudioContextConstructor(): typeof AudioContext {
  return (
    window.AudioContext ||
    (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
  );
}

function getSharedAudioContext(): AudioContext {
  if (!sharedAudioContext || sharedAudioContext.state === "closed") {
    const AudioCtx = getAudioContextConstructor();
    sharedAudioContext = new AudioCtx();
  }
  attachFirstGestureUnlocker();
  return sharedAudioContext;
}

function attachFirstGestureUnlocker(): void {
  if (gestureListenerAttached || typeof window === "undefined") return;
  gestureListenerAttached = true;

  const unlockOnGesture = () => {
    const ctx = sharedAudioContext;
    if (ctx && ctx.state === "suspended") {
      void ctx.resume().catch(() => {});
    }
    if (!ctx || ctx.state === "running") {
      window.removeEventListener("pointerdown", unlockOnGesture);
      window.removeEventListener("keydown", unlockOnGesture);
      gestureListenerAttached = false;
    }
  };

  window.addEventListener("pointerdown", unlockOnGesture, { passive: true });
  window.addEventListener("keydown", unlockOnGesture, { passive: true });
}

function pickSpanishVoice(): SpeechSynthesisVoice | null {
  if (!("speechSynthesis" in window)) return null;
  const voices = window.speechSynthesis.getVoices();
  return (
    voices.find((v) => v.lang.toLowerCase() === "es-co") ??
    voices.find((v) => v.lang.toLowerCase().startsWith("es-419")) ??
    voices.find((v) => v.lang.toLowerCase().startsWith("es-es")) ??
    voices.find((v) => v.lang.toLowerCase().startsWith("es")) ??
    null
  );
}

export class AuraAudioPlayerAdapter {
  private activeSource: AudioBufferSourceNode | null = null;
  private rafId: number | null = null;
  private activeRunId = 0;

  constructor() {
    if (typeof window !== "undefined") {
      attachFirstGestureUnlocker();
    }
  }

  async unlock(): Promise<boolean> {
    const ctx = getSharedAudioContext();
    if (ctx.state === "suspended") {
      await ctx.resume().catch(() => {});
    }
    return ctx.state === "running";
  }

  async playPrompt(
    fetchTtsBlob: () => Promise<Blob>,
    fallbackText: string,
    onFrame: AudioLevelListener,
  ): Promise<AudioPlaybackOutcome> {
    this.stop(onFrame);
    const runId = ++this.activeRunId;
    const isRunning = await this.unlock();

    if (!isRunning) {
      return "blocked";
    }

    try {
      const blob = await fetchTtsBlob();
      if (runId !== this.activeRunId) return "tts";
      await this.playBlobWithAnalyser(blob, runId, onFrame);
      return "tts";
    } catch (error) {
      console.warn(
        "[AURA TTS] Falló la reproducción desde /tts; activando fallback speechSynthesis:",
        error,
      );
      if (runId !== this.activeRunId) return "web-speech";
      await this.playWebSpeechFallback(fallbackText, runId, onFrame);
      return "web-speech";
    }
  }

  stop(onFrame?: AudioLevelListener): void {
    this.activeRunId += 1;
    if (this.rafId !== null) {
      window.cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    if (this.activeSource) {
      try {
        this.activeSource.stop();
      } catch {
        // Fuente ya detenida
      }
      this.activeSource.disconnect();
      this.activeSource = null;
    }
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    onFrame?.(0, new Array<number>(BIN_COUNT).fill(0));
  }

  dispose(): void {
    // Mantiene sharedAudioContext vivo entre turnos y recargas suaves sin perder permiso autoplay.
    this.stop();
  }

  private async playBlobWithAnalyser(
    blob: Blob,
    runId: number,
    onFrame: AudioLevelListener,
  ): Promise<void> {
    const ctx = getSharedAudioContext();
    if (ctx.state === "suspended") {
      await ctx.resume().catch(() => {});
    }
    const audioBuffer = await ctx.decodeAudioData(await blob.arrayBuffer());
    if (runId !== this.activeRunId) return;
    if (ctx.state === "suspended") {
      await ctx.resume().catch(() => {});
    }

    const analyser = ctx.createAnalyser();
    analyser.fftSize = 128;
    analyser.smoothingTimeConstant = 0.78;

    const source = ctx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(analyser);
    analyser.connect(ctx.destination);
    this.activeSource = source;

    const freqData = new Uint8Array(analyser.frequencyBinCount);
    await new Promise<void>((resolve) => {
      const tick = () => {
        if (runId !== this.activeRunId || this.activeSource !== source) return;
        analyser.getByteFrequencyData(freqData);
        const bins = new Array<number>(BIN_COUNT);
        let sum = 0;
        const limit = Math.min(BIN_COUNT, freqData.length);
        for (let i = 0; i < BIN_COUNT; i += 1) {
          const val = i < limit ? freqData[i] / 255 : 0;
          bins[i] = val;
          sum += val;
        }
        onFrame(Math.min(1, (sum / BIN_COUNT) * 1.65), bins);
        this.rafId = window.requestAnimationFrame(tick);
      };

      source.onended = () => {
        if (this.rafId !== null) {
          window.cancelAnimationFrame(this.rafId);
          this.rafId = null;
        }
        if (this.activeSource === source) {
          this.activeSource = null;
        }
        onFrame(0, new Array<number>(BIN_COUNT).fill(0));
        resolve();
      };

      source.start(0);
      this.rafId = window.requestAnimationFrame(tick);
    });
  }

  private async playWebSpeechFallback(
    text: string,
    runId: number,
    onFrame: AudioLevelListener,
  ): Promise<void> {
    if (!("speechSynthesis" in window) || !text.trim()) return;

    await new Promise<void>((resolve) => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "es-CO";
      utterance.rate = 1.0;
      const voice = pickSpanishVoice();
      if (voice) utterance.voice = voice;

      const startedAt = performance.now();
      const animate = (now: number) => {
        if (runId !== this.activeRunId) return;
        const elapsed = (now - startedAt) / 1000;
        const level = 0.25 + 0.22 * Math.abs(Math.sin(elapsed * 5.2));
        const bins = Array.from({ length: BIN_COUNT }, (_, idx) =>
          Math.max(0.06, Math.min(1, level * (0.65 + 0.55 * Math.sin(elapsed * 7 + idx * 0.45)))),
        );
        onFrame(level, bins);
        this.rafId = window.requestAnimationFrame(animate);
      };

      const finish = () => {
        if (this.rafId !== null) {
          window.cancelAnimationFrame(this.rafId);
          this.rafId = null;
        }
        onFrame(0, new Array<number>(BIN_COUNT).fill(0));
        resolve();
      };

      utterance.onend = finish;
      utterance.onerror = finish;
      this.rafId = window.requestAnimationFrame(animate);
      window.speechSynthesis.speak(utterance);
    });
  }
}
