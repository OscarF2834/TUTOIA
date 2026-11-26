import { useState, type FormEvent } from "react";
import { FileSearch, Sparkles } from "lucide-react";
import type { FdcModality, FdcType, FdcUploadRequest } from "@/domain/models/fdc";
import {
  ALLOWED_FDC_EXTENSIONS,
  FDC_TYPE_LABELS,
  MAX_FDC_FILE_SIZE_MB,
  MODALITY_LABELS,
  validateFdcFile,
} from "@/domain/rules/fdcFileRules";
import {
  Badge,
  Button,
  Card,
  FileDropzone,
  Input,
  Select,
  type DropzoneStatus,
} from "@/presentation/components/ui";

export interface FdcUploadFormProps {
  isSubmitting: boolean;
  onSubmit: (request: FdcUploadRequest) => void;
}

const FDC_TYPE_OPTIONS = [
  { value: "FDC_125", label: FDC_TYPE_LABELS.FDC_125 },
  { value: "FDC_124", label: FDC_TYPE_LABELS.FDC_124 },
];

const MODALITY_OPTIONS = [
  { value: "DESARROLLO_TECNOLOGICO", label: MODALITY_LABELS.DESARROLLO_TECNOLOGICO },
  { value: "INVESTIGACION", label: MODALITY_LABELS.INVESTIGACION },
  { value: "MONOGRAFIA", label: MODALITY_LABELS.MONOGRAFIA },
  { value: "EMPRENDIMIENTO", label: MODALITY_LABELS.EMPRENDIMIENTO },
];

export function FdcUploadForm({ isSubmitting, onSubmit }: FdcUploadFormProps) {
  const [fdcType, setFdcType] = useState<FdcType>("FDC_125");
  const [academicProgram, setAcademicProgram] = useState("");
  const [modality, setModality] = useState<FdcModality | "">("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | undefined>(undefined);

  const handleFileSelect = (file: File) => {
    const validationError = validateFdcFile(file);
    if (validationError) {
      setSelectedFile(null);
      setFileError(validationError);
      return;
    }
    setFileError(undefined);
    setSelectedFile(file);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile || fileError || isSubmitting) return;
    onSubmit({
      file: selectedFile,
      fdcType,
      academicProgram: academicProgram.trim() || undefined,
      modality: modality || undefined,
    });
  };

  const dropzoneStatus: DropzoneStatus = isSubmitting
    ? "analyzing"
    : fileError
      ? "error"
      : selectedFile
        ? "ready"
        : "idle";

  return (
    <Card
      title="Carga y diagnóstico de documento FDC"
      subtitle="Sube la propuesta (F-DC-124) o el informe final (F-DC-125) de las UTS para extraer su estructura académica y detectar focos de sustentación."
      headerAction={
        <Badge variant="brand" dot>
          Módulo 1 · Ingesta Multimodal
        </Badge>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Select
            label="Formato institucional"
            options={FDC_TYPE_OPTIONS}
            value={fdcType}
            disabled={isSubmitting}
            onChange={(event) => setFdcType(event.target.value as FdcType)}
            helperText="Define las reglas mínimas de estructura UTS a validar."
          />

          <Input
            label="Programa académico (opcional)"
            value={academicProgram}
            disabled={isSubmitting}
            onChange={(event) => setAcademicProgram(event.target.value)}
            placeholder="Opcional: se extrae automáticamente del FDC"
            helperText="Si se deja vacío, AURA lo detecta del encabezado."
          />

          <Select
            label="Modalidad (opcional)"
            options={MODALITY_OPTIONS}
            placeholder="Detectar desde el documento"
            value={modality}
            disabled={isSubmitting}
            onChange={(event) => setModality(event.target.value as FdcModality | "")}
            helperText="Orienta el énfasis técnico o investigativo del análisis."
          />
        </div>

        <FileDropzone
          label="Archivo del trabajo de grado (.pdf o .docx)"
          accept={[...ALLOWED_FDC_EXTENSIONS]}
          maxSizeMb={MAX_FDC_FILE_SIZE_MB}
          selectedFile={selectedFile}
          status={dropzoneStatus}
          errorMessage={fileError}
          disabled={isSubmitting}
          onFileSelect={handleFileSelect}
          onClear={() => {
            setSelectedFile(null);
            setFileError(undefined);
          }}
        />

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-4">
          <p className="flex items-center gap-1.5 text-xs text-slate-500">
            <Sparkles className="h-3.5 w-3.5 text-emerald-700" aria-hidden="true" />
            <span>Validación en cadena + indexación única en Gemini Files API.</span>
          </p>
          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={isSubmitting}
            disabled={!selectedFile || Boolean(fileError)}
            leftIcon={<FileSearch className="h-4 w-4" />}
          >
            {isSubmitting ? "Analizando documento…" : "Analizar documento FDC"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
