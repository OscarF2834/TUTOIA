import type {
  ActaExportFormat,
  CreateDefenseSessionRequest,
  DefenseSession,
  DownloadedActaFile,
  TurnSubmissionResult,
} from "@/domain/models/defense";

export interface IDefenseApi {
  createSession(request: CreateDefenseSessionRequest, signal?: AbortSignal): Promise<DefenseSession>;
  getSession(sessionId: string, signal?: AbortSignal): Promise<DefenseSession>;
  synthesizeSpeech(sessionId: string, text?: string, signal?: AbortSignal): Promise<Blob>;
  submitAudioTurn(
    sessionId: string,
    audioBlob: Blob,
    filename: string,
    signal?: AbortSignal,
  ): Promise<TurnSubmissionResult>;
  submitTextTurn(
    sessionId: string,
    text: string,
    signal?: AbortSignal,
  ): Promise<TurnSubmissionResult>;
  downloadActaReport(
    sessionId: string,
    format: ActaExportFormat,
    signal?: AbortSignal,
  ): Promise<DownloadedActaFile>;
}
