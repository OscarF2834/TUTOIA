import type { ReactNode } from "react";
import { cn } from "./cn";

export interface CardProps {
  title?: string;
  subtitle?: string;
  headerAction?: ReactNode;
  footer?: ReactNode;
  padding?: "none" | "sm" | "md" | "lg";
  className?: string;
  children: ReactNode;
}

const PADDING_CLASSES = {
  none: "",
  sm: "p-4",
  md: "p-5 sm:p-6",
  lg: "p-6 sm:p-8",
};

export function Card({
  title,
  subtitle,
  headerAction,
  footer,
  padding = "md",
  className,
  children,
}: CardProps) {
  const hasHeader = Boolean(title || subtitle || headerAction);

  return (
    <section
      className={cn(
        "rounded-xl border border-slate-200 bg-white shadow-sm",
        className,
      )}
    >
      {hasHeader && (
        <header className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 px-5 py-4 sm:px-6">
          <div>
            {title && <h2 className="text-base font-semibold tracking-tight text-slate-900">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs sm:text-sm text-slate-500">{subtitle}</p>}
          </div>
          {headerAction && <div className="shrink-0">{headerAction}</div>}
        </header>
      )}
      <div className={PADDING_CLASSES[padding]}>{children}</div>
      {footer && (
        <footer className="border-t border-slate-200 bg-slate-50/80 px-5 py-3.5 sm:px-6 rounded-b-xl">
          {footer}
        </footer>
      )}
    </section>
  );
}
