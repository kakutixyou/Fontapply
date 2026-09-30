export interface HttpClientInit {
  baseUrl?: string;
  timeoutMs?: number;
  retries?: number;
}

export class HttpClientError extends Error {
  readonly status?: number;
  readonly detail?: unknown;
  readonly isTimeout: boolean;
  readonly isNetworkError: boolean;

  constructor(
    message: string,
    options?: { status?: number; detail?: unknown; isTimeout?: boolean; isNetworkError?: boolean },
  ) {
    super(message);
    this.name = 'HttpClientError';
    this.status = options?.status;
    this.detail = options?.detail;
    this.isTimeout = options?.isTimeout ?? false;
    this.isNetworkError = options?.isNetworkError ?? false;
  }
}

interface HttpClientConfig {
  baseUrl: string;
  timeoutMs: number;
  retries: number;
}

const DEFAULT_HTTP_CONFIG: HttpClientConfig = {
  baseUrl: 'http://localhost:8000',
  timeoutMs: 30_000,
  retries: 2,
};

let httpConfig: HttpClientConfig = { ...DEFAULT_HTTP_CONFIG };

export function initHttpClient(init?: HttpClientInit): void {
  httpConfig = {
    baseUrl: (init?.baseUrl ?? DEFAULT_HTTP_CONFIG.baseUrl).replace(/\/+$/, ''),
    timeoutMs: init?.timeoutMs ?? DEFAULT_HTTP_CONFIG.timeoutMs,
    retries: init?.retries ?? DEFAULT_HTTP_CONFIG.retries,
  };
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function shouldRetry(error: unknown, attempt: number): boolean {
  if (attempt >= httpConfig.retries) {
    return false;
  }

  if (error instanceof HttpClientError) {
    if (error.isTimeout || error.isNetworkError) {
      return true;
    }
    if (typeof error.status === 'number') {
      return error.status === 429 || error.status >= 500;
    }
  }
  return false;
}

function buildUrl(path: string): string {
  if (/^https?:\/\//.test(path)) {
    return path;
  }
  return `${httpConfig.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
}

async function toHttpClientError(response: Response): Promise<HttpClientError> {
  let detail: unknown;
  try {
    detail = await response.json();
  } catch {
    detail = await response.text().catch(() => '');
  }

  const message =
    typeof detail === 'object' && detail !== null && 'detail' in detail
      ? String((detail as { detail?: string }).detail ?? response.statusText)
      : String(detail || response.statusText || 'Unknown backend error');

  return new HttpClientError(`HTTP ${response.status}: ${message}`, {
    status: response.status,
    detail,
  });
}

async function request(path: string, init: RequestInit): Promise<Response> {
  const url = buildUrl(path);

  for (let attempt = 0; ; attempt += 1) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), httpConfig.timeoutMs);

    try {
      const response = await fetch(url, {
        ...init,
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          ...init.headers,
        },
      });

      if (!response.ok) {
        throw await toHttpClientError(response);
      }

      return response;
    } catch (error) {
      const normalizedError =
        error instanceof HttpClientError
          ? error
          : error instanceof Error && error.name === 'AbortError'
            ? new HttpClientError(`Request timeout after ${httpConfig.timeoutMs}ms: ${url}`, {
                isTimeout: true,
              })
            : new HttpClientError(
                `Network request failed: ${error instanceof Error ? error.message : String(error)}`,
                { isNetworkError: true },
              );

      if (shouldRetry(normalizedError, attempt)) {
        await sleep(250 * (attempt + 1));
        continue;
      }

      throw normalizedError;
    } finally {
      clearTimeout(timeoutId);
    }
  }
}

export async function postJson<TResponse>(path: string, body: unknown): Promise<TResponse> {
  const response = await request(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  return (await response.json()) as TResponse;
}

export async function getBlob(path: string): Promise<Blob> {
  const response = await request(path, {
    method: 'GET',
    headers: {
      Accept: 'image/png',
    },
  });

  return response.blob();
}
