/**
 * API Client — connects the Next.js Frontend to the FastAPI Backend.
 *
 * All Backend calls go through this module so the base URL
 * is configured in one place.
 *
 * Author: brandyxie
 * Email:  brandyxie100@qq.com
 */

import type {
  CVUploadResponse,
  CVAnalysisResult,
  AgentQueryRequest,
  AgentQueryResponse,
  HealthResponse,
} from "@/types";

/** Backend base URL — reads from env var or defaults to localhost:8000 */
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/** Health check */
export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  return handleResponse<HealthResponse>(res);
}

/** Upload a CV file (PDF / DOCX / TXT). */
export async function uploadCV(file: File): Promise<CVUploadResponse> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: form,
  });
  return handleResponse<CVUploadResponse>(res);
}

/** Run the full analysis pipeline on an uploaded CV. */
export async function analyzeCV(fileId: string): Promise<CVAnalysisResult> {
  const res = await fetch(`${API_BASE}/analyze/${fileId}`);
  return handleResponse<CVAnalysisResult>(res);
}

/** Ask the LangChain agent a free-form question about a CV. */
export async function queryAgent(
  req: AgentQueryRequest
): Promise<AgentQueryResponse> {
  const res = await fetch(`${API_BASE}/agent/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return handleResponse<AgentQueryResponse>(res);
}
