export type DemoUser =
  | "aster-admin" | "aster-designer" | "aster-procurement"
  | "aster-pm" | "rival-admin" | "rival-designer";

export type Document = {
  id: string;
  filename: string;
  project_code: string | null;
  status: "queued" | "processing" | "ready" | "failed" | string;
  chunk_count: number;
  error_code: string | null;
  created_at: string;
};
export type Citation = {
  document_id: string;
  chunk_id: string;
  filename: string;
  project_code: string | null;
  source: Record<string, unknown>;
  supporting_quote: string;
};
export type Evidence = {
  chunk_id: string;
  document_id: string;
  filename: string;
  project_code: string | null;
  text: string;
  source: Record<string, unknown>;
  rrf_score: number;
  rerank_score: number;
};
export type Retrieval = {
  keyword_candidates?: number;
  vector_candidates?: number;
  reranked?: boolean;
  latency_ms?: number;
  note?: string;
};
export type AnswerResponse = {
  status: "answered" | "insufficient_evidence";
  answer: string;
  citations: Citation[];
  citation_integrity: string;
  reason: string | null;
  retrieval: Retrieval;
  usage?: { input_tokens?: number | null; output_tokens?: number | null; model?: string };
};
export type SearchResponse = { results: Evidence[]; retrieval: Retrieval };

export async function request<T>(
  path: string,
  user: DemoUser,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("x-demo-user", user);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("content-type", "application/json");
  }
  const result = await fetch(`/api/gateway/${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  const json: unknown = await result.json().catch(() => ({}));
  if (!result.ok) {
    const data = json as { detail?: string | { message?: string } };
    const detail = typeof data.detail === "string"
      ? data.detail
      : data.detail?.message || `Request failed (${result.status})`;
    throw new Error(detail);
  }
  return json as T;
}

export function humanSource(source: Record<string, unknown> | undefined): string {
  if (!source) return "Source location unavailable";
  const parts: string[] = [];
  for (const [key, label] of [
    ["page", "Page"], ["page_number", "Page"],
    ["sheet", "Sheet"], ["cell_range", "Cells"],
    ["heading", "Section"], ["section", "Section"],
    ["paragraph", "Paragraph"], ["row_range", "Rows"],
  ]) {
    const value = source[key];
    if (value !== undefined && value !== null && value !== "") {
      parts.push(`${label}: ${String(value)}`);
    }
  }
  if (parts.length > 0) return [...new Set(parts)].join(" · ");
  const asText = Object.entries(source)
    .filter(([, val]) => typeof val === "string" || typeof val === "number")
    .map(([key, val]) => `${key.replaceAll("_", " ")}: ${String(val)}`);
  return asText.slice(0, 3).join(" · ") || "Document excerpt";
}
