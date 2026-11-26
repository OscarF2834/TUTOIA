import { useCallback, useEffect, useRef, useState } from "react";
import type { FdcDocumentResult, FdcErrorInfo, FdcType, FdcUploadRequest } from "@/domain/models/fdc";
import { mapApiErrorToUserFeedback } from "@/domain/rules/fdcFileRules";
import { ApiHttpError } from "@/infrastructure/api/httpClient";
import { tutoiaApi } from "@/infrastructure/api/TutoiaApiFacade";

const STORAGE_KEY = "tutoia.fdc.lastDocumentId";

export type IngestionViewStatus = "idle" | "hydrating" | "analyzing" | "success" | "error";

function toErrorInfo(err: unknown): FdcErrorInfo {
  if (err instanceof ApiHttpError) {
    return mapApiErrorToUserFeedback(err.status, err.detail, err.code, err.context);
  }
  const message = err instanceof Error ? err.message : "Error inesperado al procesar la solicitud.";
  return mapApiErrorToUserFeedback(0, message, "UNEXPECTED_ERROR");
}

export function useFdcIngestion() {
  const [status, setStatus] = useState<IngestionViewStatus>("idle");
  const [stageIndex, setStageIndex] = useState(0);
  const [progressPercent, setProgressPercent] = useState(0);
  const [activeFdcType, setActiveFdcType] = useState<FdcType>("FDC_125");
  const [result, setResult] = useState<FdcDocumentResult | null>(null);
  const [error, setError] = useState<FdcErrorInfo | null>(null);

  const lastRequestRef = useRef<FdcUploadRequest | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const savedId = window.sessionStorage.getItem(STORAGE_KEY);
    if (!savedId) return undefined;

    const controller = new AbortController();
    setStatus("hydrating");

    tutoiaApi
      .getFdcById(savedId, controller.signal)
      .then((doc) => {
        setResult(doc);
        setActiveFdcType(doc.fdcType);
        setStatus("success");
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        window.sessionStorage.removeItem(STORAGE_KEY);
        setStatus("idle");
      });

    return () => controller.abort();
  }, []);

  const submitUpload = useCallback(async (request: FdcUploadRequest) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    lastRequestRef.current = request;
    setActiveFdcType(request.fdcType);
    setStatus("analyzing");
    setError(null);
    setStageIndex(0);
    setProgressPercent(22);

    const t1 = window.setTimeout(() => {
      setStageIndex(1);
      setProgressPercent(52);
    }, 900);
    const t2 = window.setTimeout(() => {
      setStageIndex(2);
      setProgressPercent(82);
    }, 2200);

    try {
      const response = await tutoiaApi.uploadFdc(request, controller.signal);
      window.clearTimeout(t1);
      window.clearTimeout(t2);
      setProgressPercent(100);
      setResult(response);
      setStatus("success");
      window.sessionStorage.setItem(STORAGE_KEY, response.documentId);
    } catch (err) {
      window.clearTimeout(t1);
      window.clearTimeout(t2);
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError(toErrorInfo(err));
      setStatus("error");
    }
  }, []);

  const retryLastUpload = useCallback(() => {
    if (lastRequestRef.current) {
      void submitUpload(lastRequestRef.current);
    }
  }, [submitUpload]);

  const resetForNewUpload = useCallback(() => {
    abortRef.current?.abort();
    window.sessionStorage.removeItem(STORAGE_KEY);
    lastRequestRef.current = null;
    setResult(null);
    setError(null);
    setStageIndex(0);
    setProgressPercent(0);
    setStatus("idle");
  }, []);

  return {
    status,
    stageIndex,
    progressPercent,
    activeFdcType,
    result,
    error,
    submitUpload,
    retryLastUpload,
    resetForNewUpload,
  };
}
