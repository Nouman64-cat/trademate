import type {
  HealthResponse,
  IngestResponse,
  JobStatusResponse,
  UploadResponse,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Request failed: ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  /** Upload a local file to S3. Returns the S3 key. */
  async uploadFile(file: File): Promise<UploadResponse> {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE_URL}/upload`, {
      method: "POST",
      body: form,
      // No Content-Type header — browser sets multipart boundary automatically
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.detail ?? `Upload failed: ${res.status}`);
    }
    return res.json() as Promise<UploadResponse>;
  },

  ingest(s3Key: string): Promise<IngestResponse> {
    return request<IngestResponse>("/ingest", {
      method: "POST",
      body: JSON.stringify({ s3_key: s3Key }),
    });
  },

  getJob(jobId: string): Promise<JobStatusResponse> {
    return request<JobStatusResponse>(`/ingest/${jobId}`);
  },

  health(): Promise<HealthResponse> {
    return request<HealthResponse>("/health");
  },
};
