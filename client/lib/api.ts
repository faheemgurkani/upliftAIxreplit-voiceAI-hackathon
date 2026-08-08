import type {
  ClusterDetail,
  ClusterSummary,
  HealthResponse,
  KpiResponse,
  ReviewPayload,
  SessionCreateResponse,
  StatementDetail,
  StatementsResponse,
} from "./types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(
  /\/$/,
  ""
);

export function getApiUrl() {
  return API_URL;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || body.error || JSON.stringify(body);
    } catch {
      /* keep statusText */
    }
    throw new Error(`${res.status}: ${detail}`);
  }

  if (res.status === 204) return undefined as T;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return res.json() as Promise<T>;
  }
  return res as unknown as T;
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function getKpis(): Promise<KpiResponse> {
  return request<KpiResponse>("/api/kpis");
}

export async function listStatements(params?: {
  status?: string;
  page?: number;
  flags?: string;
}): Promise<StatementsResponse> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.page) qs.set("page", String(params.page));
  if (params?.flags) qs.set("flags", params.flags);
  const query = qs.toString();
  return request<StatementsResponse>(
    `/api/dashboard/statements${query ? `?${query}` : ""}`
  );
}

export async function getStatement(refCode: string): Promise<StatementDetail> {
  return request<StatementDetail>(`/api/statements/${encodeURIComponent(refCode)}`);
}

export async function reviewStatement(
  refCode: string,
  payload: ReviewPayload
): Promise<StatementDetail> {
  return request<StatementDetail>(
    `/api/statements/${encodeURIComponent(refCode)}/review`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function getStatementAudioUrl(refCode: string): string {
  return `${API_URL}/api/statements/${encodeURIComponent(refCode)}/audio`;
}

export async function createSession(body?: {
  participantName?: string;
}): Promise<SessionCreateResponse> {
  return request<SessionCreateResponse>("/api/sessions/create", {
    method: "POST",
    body: JSON.stringify(body || { participantName: "Witness" }),
  });
}

export async function listClusters(): Promise<{ items: ClusterSummary[] } | ClusterSummary[]> {
  return request(`/api/dashboard/clusters`);
}

export async function getCluster(clusterId: string): Promise<ClusterDetail> {
  return request<ClusterDetail>(
    `/api/dashboard/clusters/${encodeURIComponent(clusterId)}`
  );
}

export function normalizeClusters(
  data: { items: ClusterSummary[] } | ClusterSummary[]
): ClusterSummary[] {
  return Array.isArray(data) ? data : data.items || [];
}
