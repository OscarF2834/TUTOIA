export class ApiHttpError extends Error {
  readonly status: number;
  readonly code: string;
  readonly detail: string;
  readonly context: Record<string, unknown>;

  constructor(
    status: number,
    code: string,
    detail: string,
    context: Record<string, unknown> = {},
  ) {
    super(detail);
    this.name = "ApiHttpError";
    this.status = status;
    this.code = code;
    this.detail = detail;
    this.context = context;
  }
}

function extractFastApiDetail(rawDetail: unknown, fallback: string): string {
  if (typeof rawDetail === "string" && rawDetail.trim()) {
    return rawDetail;
  }
  if (Array.isArray(rawDetail) && rawDetail.length > 0) {
    const first = rawDetail[0] as { msg?: unknown };
    if (typeof first?.msg === "string") {
      return first.msg;
    }
  }
  return fallback;
}

async function executeFetch(url: string, options: RequestInit = {}): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(url, options);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiHttpError(
      0,
      "NETWORK_ERROR",
      "No fue posible conectar con el backend de TutoIA. Verifique que FastAPI esté en ejecución.",
    );
  }

  if (!response.ok) {
    let code = `HTTP_${response.status}`;
    let detail = `Error HTTP ${response.status}`;
    let context: Record<string, unknown> = {};
    try {
      const body = (await response.json()) as {
        detail?: unknown;
        code?: unknown;
        context?: unknown;
      };
      detail = extractFastApiDetail(body.detail, detail);
      if (typeof body.code === "string" && body.code.trim()) {
        code = body.code;
      }
      if (body.context && typeof body.context === "object" && !Array.isArray(body.context)) {
        context = body.context as Record<string, unknown>;
      }
    } catch {
      // Respuesta sin cuerpo JSON válido
    }
    throw new ApiHttpError(response.status, code, detail, context);
  }

  return response;
}

export async function httpRequest<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await executeFetch(url, options);
  return (await response.json()) as T;
}

export async function requestBlob(url: string, options: RequestInit = {}): Promise<Blob> {
  const response = await executeFetch(url, options);
  return await response.blob();
}

export async function requestBlobWithMeta(
  url: string,
  options: RequestInit = {},
): Promise<{ blob: Blob; contentDisposition: string | null }> {
  const response = await executeFetch(url, options);
  return {
    blob: await response.blob(),
    contentDisposition: response.headers.get("Content-Disposition"),
  };
}
