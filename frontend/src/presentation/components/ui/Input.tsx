import { useId, type InputHTMLAttributes, type ReactNode } from "react";
import { cn } from "./cn";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
  leftAddon?: ReactNode;
  rightAddon?: ReactNode;
}

export function Input({
  label,
  helperText,
  error,
  leftAddon,
  rightAddon,
  id,
  className,
  ...rest
}: InputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const helpId = `${inputId}-help`;
  const errorId = `${inputId}-error`;
  const describedBy = error ? errorId : helperText ? helpId : undefined;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="mb-1.5 block text-xs font-semibold normal-case tracking-normal text-slate-700"
        >
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {leftAddon && (
          <span className="pointer-events-none absolute left-3 text-slate-400">{leftAddon}</span>
        )}
        <input
          id={inputId}
          aria-invalid={Boolean(error)}
          aria-describedby={describedBy}
          className={cn(
            "w-full rounded-lg border bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400",
            "transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-1",
            error
              ? "border-rose-400 focus:border-rose-500 focus-visible:ring-rose-500"
              : "border-slate-300 hover:border-slate-400 focus:border-emerald-600",
            Boolean(leftAddon) && "pl-9",
            Boolean(rightAddon) && "pr-9",
            className,
          )}
          {...rest}
        />
        {rightAddon && (
          <span className="pointer-events-none absolute right-3 text-slate-400">{rightAddon}</span>
        )}
      </div>
      {error ? (
        <p id={errorId} className="mt-1.5 text-xs font-medium text-rose-700">
          {error}
        </p>
      ) : helperText ? (
        <p id={helpId} className="mt-1.5 text-xs text-slate-500">
          {helperText}
        </p>
      ) : null}
    </div>
  );
}
