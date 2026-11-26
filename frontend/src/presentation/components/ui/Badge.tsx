import type { ReactNode } from "react";
import { cn } from "./cn";

export type BadgeVariant = "neutral" | "brand" | "info" | "success" | "warning" | "danger";

export interface BadgeProps {
  variant?: BadgeVariant;
  size?: "sm" | "md";
  dot?: boolean;
  className?: string;
  children: ReactNode;
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  neutral: "bg-slate-100 text-slate-700 border-slate-200",
  brand: "bg-emerald-50 text-emerald-800 border-emerald-200",
  info: "bg-sky-50 text-sky-800 border-sky-200",
  success: "bg-emerald-50 text-emerald-800 border-emerald-300",
  warning: "bg-amber-50 text-amber-800 border-amber-300",
  danger: "bg-rose-50 text-rose-800 border-rose-300",
};

const DOT_CLASSES: Record<BadgeVariant, string> = {
  neutral: "bg-slate-500",
  brand: "bg-emerald-600",
  info: "bg-sky-600",
  success: "bg-emerald-600",
  warning: "bg-amber-600",
  danger: "bg-rose-600",
};

export function Badge({
  variant = "neutral",
  size = "md",
  dot = false,
  className,
  children,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-semibold",
        size === "sm" ? "px-2.5 py-0.5 text-[11px]" : "px-3 py-1 text-xs",
        VARIANT_CLASSES[variant],
        className,
      )}
    >
      {dot && <span className={cn("h-1.5 w-1.5 rounded-full", DOT_CLASSES[variant])} aria-hidden="true" />}
      {children}
    </span>
  );
}
