import type {
  ActaExportFormat,
  CreateDefenseSessionRequest,
  DefenseSession,
  DownloadedActaFile,
  TurnSubmissionResult,
} from "@/domain/models/defense";
import type { FdcDocumentResult, FdcUploadRequest } from "@/domain/models/fdc";
import type { IDefenseApi } from "@/domain/ports/defenseApiPort";
import type { IFdcApiPort } from "@/domain/ports/fdcApiPort";
import { httpRequest, requestBlob, requestBlobWithMeta } from "@/infrastructure/api/httpClient";
import {
  mapDefenseSessionDtoToDomain,
  mapTurnSubmissionDtoToDomain,
  type DefenseSessionResponseDto,
  type TurnSubmissionResponseDto,
} from "@/infrastructure/api/mappers/defenseMapper";
import {
  mapFdcResponseDtoToDomain,
  type FdcDocumentResponseDto,
} from "@/infrastructure/api/mappers/fdcMapper";

export class TutoiaApiFacade implements IFdcApiPort, IDefenseApi {
  async uploadFdc(request: FdcUploadRequest, signal?: AbortSignal): Promise<FdcDocumentResult> {
    const formData = new FormData();
    formData.append("file", request.file);
    formData.append("fdc_type", request.fdcType);

    const trimmedProgram = request.academicProgram?.trim();
    if (trimmedProgram) {
      formData.append("academic_program", trimmedProgram);
    }
    if (request.modality) {
      formData.append("modality", request.modality);
    }

    const dto = await httpRequest<FdcDocumentResponseDto>("/api/v1/fdc/upload", {
      method: "POST",
      body: formData,
      signal,
    });
    return mapFdcResponseDtoToDomain(dto);
  }

  async getFdcById(documentId: string, signal?: AbortSignal): Promise<FdcDocumentResult> {
    const dto = await httpRequest<FdcDocumentResponseDto>(
      `/api/v1/fdc/${encodeURIComponent(documentId)}`,
      { signal },
    );
    return mapFdcResponseDtoToDomain(dto);
  }

  async createSession(
    request: CreateDefenseSessionRequest,
    signal?: AbortSignal,
  ): Promise<DefenseSession> {
    const dto = await httpRequest<DefenseSessionResponseDto>("/api/v1/defense/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        fdc_document_id: request.fdcDocumentId,
        jury_profile: request.juryProfile,
      }),
      signal,
    });
    return mapDefenseSessionDtoToDomain(dto);
  }

  async getSession(sessionId: string, signal?: AbortSignal): Promise<DefenseSession> {
    const dto = await httpRequest<DefenseSessionResponseDto>(
      `/api/v1/defense/sessions/${encodeURIComponent(sessionId)}`,
      { signal },
    );
    return mapDefenseSessionDtoToDomain(dto);
  }

  async synthesizeSpeech(sessionId: string, text?: string, signal?: AbortSignal): Promise<Blob> {
    const cleanText = text?.trim();
    return requestBlob(`/api/v1/defense/sessions/${encodeURIComponent(sessionId)}/tts`, {
      method: "POST",
      headers: cleanText ? { "Content-Type": "application/json" } : undefined,
      body: cleanText ? JSON.stringify({ text: cleanText }) : undefined,
      signal,
    });
  }

  async submitAudioTurn(
    sessionId: string,
    audioBlob: Blob,
    filename: string,
    signal?: AbortSignal,
  ): Promise<TurnSubmissionResult> {
    const formData = new FormData();
    formData.append("audio", audioBlob, filename);

    const dto = await httpRequest<TurnSubmissionResponseDto>(
      `/api/v1/defense/sessions/${encodeURIComponent(sessionId)}/turns/audio`,
      {
        method: "POST",
        body: formData,
        signal,
      },
    );
    return mapTurnSubmissionDtoToDomain(dto);
  }

  async submitTextTurn(
    sessionId: string,
    text: string,
    signal?: AbortSignal,
  ): Promise<TurnSubmissionResult> {
    const dto = await httpRequest<TurnSubmissionResponseDto>(
      `/api/v1/defense/sessions/${encodeURIComponent(sessionId)}/turns/text`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
        signal,
      },
    );
    return mapTurnSubmissionDtoToDomain(dto);
  }

  async downloadActaReport(
    sessionId: string,
    format: ActaExportFormat,
    signal?: AbortSignal,
  ): Promise<DownloadedActaFile> {
    const { blob, contentDisposition } = await requestBlobWithMeta(
      `/api/v1/defense/sessions/${encodeURIComponent(sessionId)}/report?format=${encodeURIComponent(format)}`,
      { method: "GET", signal },
    );
    const match = contentDisposition?.match(/filename="?([^"]+)"?/i);
    const fallbackName = `Acta_Sustentacion_UTS_${sessionId.slice(0, 8)}.${format}`;
    return {
      blob,
      filename: match?.[1]?.trim() || fallbackName,
    };
  }
}

export const tutoiaApi = new TutoiaApiFacade();
