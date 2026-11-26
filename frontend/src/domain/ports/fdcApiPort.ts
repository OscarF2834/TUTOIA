import type { FdcDocumentResult, FdcUploadRequest } from "@/domain/models/fdc";

export interface IFdcApiPort {
  uploadFdc(request: FdcUploadRequest, signal?: AbortSignal): Promise<FdcDocumentResult>;
  getFdcById(documentId: string, signal?: AbortSignal): Promise<FdcDocumentResult>;
}
