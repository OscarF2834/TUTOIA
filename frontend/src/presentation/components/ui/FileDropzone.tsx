import { useId, useRef, useState, type DragEvent } from "react";
import { AlertCircle, CheckCircle2, FileText, UploadCloud, X } from "lucide-react";
import { cn } from "./cn";

export type DropzoneStatus = "idle" | "dragging" | "uploading" | "analyzing" | "ready" | "error";

export interface FileDropzoneProps {
  label?: string;
  accept: string[];
  maxSizeMb: number;
  selectedFile: File | null;
  status: DropzoneStatus;
  errorMessage?: string;
  disabled?: boolean;
  onFileSelect: (file: File) => void;
  onClear?: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export function FileDropzone({
  label,
  accept,
  maxSizeMb,
  selectedFile,
  status,
  errorMessage,
  disabled = false,
  onFileSelect,
  onClear,
}: FileDropzoneProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const effectiveStatus: DropzoneStatus = isDragging ? "dragging" : status;
  const isBusy = effectiveStatus === "uploading" || effectiveStatus === "analyzing";

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    if (disabled || isBusy) return;
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) onFileSelect(dropped);
  };

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

      <input
        id={inputId}
        ref={inputRef}
        type="file"
        accept={accept.join(",")}
        disabled={disabled || isBusy}
        className="sr-only"
        onChange={(event) => {
          const picked = event.target.files?.[0];
          if (picked) onFileSelect(picked);
          event.target.value = "";
        }}
      />

      {selectedFile && effectiveStatus !== "error" ? (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50/50 px-4 py-3.5">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
              {effectiveStatus === "ready" ? (
                <CheckCircle2 className="h-5 w-5" />
              ) : (
                <FileText className="h-5 w-5" />
              )}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900" title={selectedFile.name}>
                {selectedFile.name}
              </p>
              <p className="text-xs text-slate-600 tabular-nums">{formatBytes(selectedFile.size)}</p>
            </div>
          </div>
          {!isBusy && onClear && (
            <button
              type="button"
              onClick={onClear}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600"
            >
              <X className="h-3.5 w-3.5" />
              Cambiar
            </button>
          )}
        </div>
      ) : (
        <div
          role="button"
          tabIndex={disabled || isBusy ? -1 : 0}
          onClick={() => !disabled && !isBusy && inputRef.current?.click()}
          onKeyDown={(event) => {
            if ((event.key === "Enter" || event.key === " ") && !disabled && !isBusy) {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(event) => {
            event.preventDefault();
            if (!disabled && !isBusy) setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2",
            effectiveStatus === "error"
              ? "border-rose-300 bg-rose-50/60 hover:border-rose-400"
              : effectiveStatus === "dragging"
                ? "border-emerald-600 bg-emerald-50/70"
                : "border-slate-300 bg-slate-50/70 hover:border-emerald-500 hover:bg-emerald-50/30",
            (disabled || isBusy) && "cursor-not-allowed opacity-60",
          )}
        >
          {effectiveStatus === "error" ? (
            <AlertCircle className="mb-2.5 h-8 w-8 text-rose-600" />
          ) : (
            <UploadCloud className="mb-2.5 h-8 w-8 text-emerald-700" />
          )}
          <p className="text-sm font-semibold text-slate-800">
            Arrastra tu documento FDC aquí o haz clic para seleccionarlo
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Formatos admitidos: <span className="font-medium text-slate-700">PDF (.pdf)</span> o{" "}
            <span className="font-medium text-slate-700">Word (.docx)</span> · Máximo{" "}
            <span className="tabular-nums font-medium text-slate-700">{maxSizeMb} MB</span>
          </p>
        </div>
      )}

      {errorMessage && (
        <p className="mt-2 flex items-center gap-1.5 text-xs font-medium text-rose-700" role="alert">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          <span>{errorMessage}</span>
        </p>
      )}
    </div>
  );
}
