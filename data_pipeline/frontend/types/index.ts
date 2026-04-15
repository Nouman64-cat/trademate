export type JobStatus = "pending" | "running" | "completed" | "failed";

export interface UploadResponse {
  s3_key: string;
  filename: string;
  size_bytes: number;
}

export interface IngestResponse {
  job_id: string;
  status: JobStatus;
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  s3_key: string;
  status: JobStatus;
  message: string;
  chunks_upserted: number;
}

export interface HealthResponse {
  status: "healthy" | "degraded";
  services: Record<string, string>;
}
