import { useId, type TextareaHTMLAttributes } from "react";
import { cn } from "./cn";

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helperText?: string;
  error?: string;
}

export function Textarea({
  label,
  helperText,
  error,
  id,
  rows = 3,
  className,
  ...rest
}: TextareaProps) {
  const generatedId = useId();
  const textareaId = id ?? generatedId;
  const helpId = `${textareaId}-help`;
  const errorId = `${textareaId}-error`;
  const describedBy = error ? errorId : helperText ? helpId : undefined;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={textareaId}
          className="mb-1.5 block text-xs font-semibold normal-case tracking-normal text-slate-700"
        >
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        rows={rows}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy}
        className={cn(
          "w-full rounded-lg border bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400",
          "transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-1",
          error
            ? "border-rose-400 focus:border-rose-500 focus-visible:ring-rose-500"
            : "border-slate-300 hover:border-slate-400 focus:border-emerald-600",
          className,
        )}
        {...rest}
      />
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
