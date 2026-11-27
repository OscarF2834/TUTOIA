import { useEffect, useRef } from "react";
import type { DefenseState } from "@/domain/models/defense";
import type { AvatarStageProps } from "@/domain/ports/avatarStageProps";
import { cn } from "@/presentation/components/ui/cn";

interface StatePalette {
  primary: string;
  secondary: string;
  glow: string;
  dotClass: string;
  speedMultiplier: number;
}

const PALETTES: Record<DefenseState, StatePalette> = {
  AURA_SPEAKING: {
    primary: "#38bdf8",
    secondary: "#0284c7",
    glow: "rgba(56, 189, 248, 0.36)",
    dotClass: "bg-sky-400",
    speedMultiplier: 1.25,
  },
  LISTENING_STUDENT: {
    primary: "#10b981",
    secondary: "#34d399",
    glow: "rgba(16, 185, 129, 0.36)",
    dotClass: "bg-emerald-400",
    speedMultiplier: 1.0,
  },
  EVALUATING_TURN: {
    primary: "#818cf8",
    secondary: "#f59e0b",
    glow: "rgba(129, 140, 248, 0.34)",
    dotClass: "bg-amber-400",
    speedMultiplier: 2.35,
  },
  PREPARING: {
    primary: "#818cf8",
    secondary: "#f59e0b",
    glow: "rgba(129, 140, 248, 0.32)",
    dotClass: "bg-indigo-400",
    speedMultiplier: 2.1,
  },
  COMPLETED: {
    primary: "#10b981",
    secondary: "#38bdf8",
    glow: "rgba(56, 189, 248, 0.25)",
    dotClass: "bg-emerald-400",
    speedMultiplier: 0.55,
  },
};

function drawSegmentedRing(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  angle: number,
  segments: number,
  gapRad: number,
  lineWidth: number,
  color: string,
): void {
  const step = (Math.PI * 2) / segments;
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.lineCap = "round";
  for (let i = 0; i < segments; i += 1) {
    const start = angle + i * step + gapRad * 0.5;
    const end = angle + (i + 1) * step - gapRad * 0.5;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, start, end);
    ctx.stroke();
  }
  ctx.restore();
}

function drawJarvisFrame(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
  state: DefenseState,
  level: number,
  bins: ReadonlyArray<number>,
): void {
  const palette = PALETTES[state];
  const cx = size / 2;
  const cy = size / 2;
  const maxR = size * 0.44;
  ctx.clearRect(0, 0, size, size);

  const bgGrad = ctx.createRadialGradient(cx, cy, maxR * 0.1, cx, cy, maxR * 1.05);
  bgGrad.addColorStop(0, palette.glow);
  bgGrad.addColorStop(0.55, "rgba(15, 23, 42, 0.35)");
  bgGrad.addColorStop(1, "rgba(2, 6, 23, 0)");
  ctx.fillStyle = bgGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, maxR * 1.05, 0, Math.PI * 2);
  ctx.fill();

  // Marcas radiales técnicas
  ctx.save();
  ctx.strokeStyle = "rgba(148, 163, 184, 0.24)";
  for (let i = 0; i < 36; i += 1) {
    const a = (i / 36) * Math.PI * 2;
    const inner = i % 3 === 0 ? maxR * 0.91 : maxR * 0.945;
    ctx.lineWidth = i % 3 === 0 ? 1.5 : 1;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(a) * inner, cy + Math.sin(a) * inner);
    ctx.lineTo(cx + Math.cos(a) * maxR, cy + Math.sin(a) * maxR);
    ctx.stroke();
  }
  ctx.restore();

  const spin = t * palette.speedMultiplier;
  drawSegmentedRing(ctx, cx, cy, maxR * 0.84, spin * 0.55, 6, 0.22, 2.5, palette.primary);
  drawSegmentedRing(ctx, cx, cy, maxR * 0.72, -spin * 0.85, 8, 0.28, 2, palette.secondary);

  // Arco de pulso interno
  ctx.save();
  ctx.strokeStyle = palette.primary;
  ctx.lineWidth = 3;
  ctx.globalAlpha = 0.75;
  ctx.beginPath();
  ctx.arc(cx, cy, maxR * 0.61, spin * 1.35, spin * 1.35 + Math.PI * (0.75 + level * 0.6));
  ctx.stroke();
  ctx.restore();

  // Corona radial reactiva a frecuencias
  const binCount = 28;
  ctx.save();
  ctx.strokeStyle = palette.secondary;
  ctx.lineCap = "round";
  ctx.lineWidth = 2.4;
  for (let i = 0; i < binCount; i += 1) {
    const angle = (i / binCount) * Math.PI * 2 - Math.PI / 2;
    const rawBin = i < bins.length ? bins[i] : 0;
    const idleWave = 0.1 + 0.08 * Math.sin(t * 2.4 + i * 0.5);
    const barAmp = Math.max(idleWave, rawBin);
    const rStart = maxR * 0.39;
    const rEnd = rStart + maxR * (0.04 + barAmp * 0.16);
    ctx.globalAlpha = 0.45 + barAmp * 0.55;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(angle) * rStart, cy + Math.sin(angle) * rStart);
    ctx.lineTo(cx + Math.cos(angle) * rEnd, cy + Math.sin(angle) * rEnd);
    ctx.stroke();
  }
  ctx.restore();

  // Núcleo central luminoso
  const coreRadius = maxR * (0.25 + level * 0.08 + 0.015 * Math.sin(t * 3));
  const coreGrad = ctx.createRadialGradient(cx, cy, 2, cx, cy, coreRadius * 1.4);
  coreGrad.addColorStop(0, "#f8fafc");
  coreGrad.addColorStop(0.45, palette.primary);
  coreGrad.addColorStop(1, "rgba(2, 6, 23, 0)");
  ctx.fillStyle = coreGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, coreRadius * 1.4, 0, Math.PI * 2);
  ctx.fill();
}

export function AuraJarvisCore({
  state,
  audioLevel,
  frequencyBins,
  statusLabel,
  subLabel,
}: AvatarStageProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const telemetryRef = useRef({ state, audioLevel, frequencyBins });
  const smoothedLevelRef = useRef(0);

  telemetryRef.current = { state, audioLevel, frequencyBins };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;
    const ctx = canvas.getContext("2d");
    if (!ctx) return undefined;

    let rafId = 0;
    const startMs = performance.now();

    const render = (now: number) => {
      const rect = canvas.getBoundingClientRect();
      const cssSize = Math.max(180, Math.min(rect.width || 240, rect.height || 240));
      const dpr = window.devicePixelRatio || 1;
      const targetPixelSize = Math.round(cssSize * dpr);

      if (canvas.width !== targetPixelSize || canvas.height !== targetPixelSize) {
        canvas.width = targetPixelSize;
        canvas.height = targetPixelSize;
      }

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const current = telemetryRef.current;
      smoothedLevelRef.current += (current.audioLevel - smoothedLevelRef.current) * 0.22;

      drawJarvisFrame(
        ctx,
        cssSize,
        (now - startMs) / 1000,
        current.state,
        smoothedLevelRef.current,
        current.frequencyBins,
      );
      rafId = window.requestAnimationFrame(render);
    };

    rafId = window.requestAnimationFrame(render);
    return () => window.cancelAnimationFrame(rafId);
  }, []);

  const palette = PALETTES[state];

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 text-slate-100 shadow-sm">
      <div className="my-2 flex items-center justify-center">
        <canvas
          ref={canvasRef}
          aria-label={`Visualizador de estado de AURA: ${statusLabel}`}
          className="h-56 w-56 sm:h-60 sm:w-60"
        />
      </div>

      <div
        aria-live="polite"
        className="flex flex-col items-center gap-1 border-t border-slate-800/90 pt-3 text-center"
      >
        <div className="inline-flex items-center gap-2 text-sm font-semibold text-white">
          <span className={cn("h-2.5 w-2.5 rounded-full", palette.dotClass)} aria-hidden="true" />
          <span>{statusLabel}</span>
        </div>
        {subLabel && <p className="text-xs text-slate-400">{subLabel}</p>}
      </div>
    </div>
  );
}
