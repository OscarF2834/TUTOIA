import type { FdcDocumentResult, FdcUploadRequest } from "@/domain/models/fdc";
import type { IFdcApiPort } from "@/domain/ports/fdcApiPort";
import { httpRequest } from "@/infrastructure/api/httpClient";
import {
  mapFdcResponseDtoToDomain,
  type FdcDocumentResponseDto,
} from "@/infrastructure/api/mappers/fdcMapper";

export class TutoiaApiFacade implements IFdcApiPort {
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
}

export const tutoiaApi = new TutoiaApiFacade();
