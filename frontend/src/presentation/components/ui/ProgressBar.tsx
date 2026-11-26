import { cn } from "./cn";

export interface ProgressBarProps {
  value: number;
  label?: string;
  tone?: "brand" | "info";
  className?: string;
}

export function ProgressBar({
  value,
  label,
  tone = "brand",
  className,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));

  return (
    <div className={cn("w-full", className)}>
      {label && (
        <div className="mb-1.5 flex items-center justify-between text-xs font-medium text-slate-700">
          <span>{label}</span>
          <span className="tabular-nums text-slate-600">{clamped}%</span>
        </div>
      )}
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={clamped}
        className="h-2.5 w-full overflow-hidden rounded-full bg-slate-200"
      >
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500 ease-out",
            tone === "info" ? "bg-sky-700" : "bg-emerald-700",
          )}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
