import { readSSE } from "./sse.ts";
import type {
  TableData, Comparison, ClaimVerification, Dashboard, DocumentMeta, EvidenceChunk, GraphData, PaperAnalysis,
  QueryResult, StreamEvent,
} from "./types.ts";

export class ApiError extends Error {
  code: string; status: number;
  constructor(code: string, message: string, status: number) {
    super(message); this.code = code; this.status = status;
  }
}

export interface ClientOptions {
  baseUrl: string;
  getToken: () => string | null;
  fetchImpl?: typeof fetch;
}

export function createClient(opts: ClientOptions) {
  const f = opts.fetchImpl ?? ((...a: Parameters<typeof fetch>) => fetch(...a));

  async function raw(path: string, init: RequestInit = {}, json?: unknown): Promise<Response> {
    const headers = new Headers(init.headers);
    const token = opts.getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (json !== undefined) { headers.set("Content-Type", "application/json"); init = { ...init, body: JSON.stringify(json) }; }
    let res: Response;
    try {
      res = await f(opts.baseUrl + path, { ...init, headers });
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") throw e;
      throw new ApiError("network", "Could not reach the server. Check your connection and retry.", 0);
    }
    if (!res.ok) {
      let code = "http_error", message = `Request failed (${res.status}).`;
      try {
        const b = await res.json() as { error?: { code: string; message: string }; detail?: string };
        if (b.error) { code = b.error.code; message = b.error.message; } else if (typeof b.detail === "string") message = b.detail;
      } catch { /* non-JSON error body */ }
      throw new ApiError(code, message, res.status);
    }
    return res;
  }
  const j = async <T>(path: string, init?: RequestInit, body?: unknown): Promise<T> =>
    (await raw(path, init, body)).json() as Promise<T>;
  const post = <T>(path: string, body: unknown) => j<T>(path, { method: "POST" }, body);

  return {
    register: (email: string, password: string) => post<{ user_id: string }>("/api/auth/register", { email, password }),
    login: (email: string, password: string) => post<{ access_token: string }>("/api/auth/login", { email, password }),
    health: () => j<{ status: string; mock_mode: boolean }>("/health"),
    documents: () => j<DocumentMeta[]>("/api/documents"),
    document: (id: string) => j<DocumentMeta>(`/api/documents/${encodeURIComponent(id)}`),
    tables: (id: string) => j<TableData[]>(`/api/documents/${encodeURIComponent(id)}/tables`),
    upload: (file: Blob, filename: string) => {
      const fd = new FormData(); fd.append("file", file, filename);
      return j<DocumentMeta>("/api/documents/upload", { method: "POST", body: fd });
    },
    query: (question: string) => post<QueryResult>("/api/research/query", { question }),
    streamChat: async (question: string, onEvent: (e: StreamEvent) => void, signal?: AbortSignal) => {
      const res = await raw("/api/chat/stream", { method: "POST", signal }, { question });
      await readSSE(res, onEvent);
    },
    analyze: (document_id: string) => post<PaperAnalysis>("/api/research/analyze", { document_id }),
    compare: (document_ids: string[]) => post<Comparison>("/api/papers/compare", { document_ids }),
    verify: (claims: string[]) => post<ClaimVerification[]>("/api/claims/verify", { claims }),
    evidence: (chunkId: string) => j<EvidenceChunk>(`/api/evidence/${encodeURIComponent(chunkId)}`),
    graph: () => j<GraphData>("/api/knowledge-graph"),
    review: (title: string, question: string) => post<{ markdown: string }>("/api/reports/literature-review", { title, question }),
    dashboard: () => j<Dashboard>("/api/dashboard"),
    evaluation: () => j<Record<string, unknown> & { evaluated: boolean }>("/api/evaluation"),
  };
}
export type Api = ReturnType<typeof createClient>;
