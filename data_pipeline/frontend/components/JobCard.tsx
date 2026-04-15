"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { JobStatusResponse } from "@/types";

const POLL_INTERVAL_MS = 2500;

const STATUS_STYLES = {
  pending: {
    pill: "bg-zinc-100 text-zinc-600",
    dot: "animate-pulse bg-zinc-400",
    label: "Pending",
  },
  running: {
    pill: "bg-blue-100 text-blue-700",
    dot: "animate-pulse bg-blue-500",
    label: "Processing…",
  },
  completed: {
    pill: "bg-green-100 text-green-700",
    dot: "bg-green-500",
    label: "Completed",
  },
  failed: {
    pill: "bg-red-100 text-red-700",
    dot: "bg-red-500",
    label: "Failed",
  },
};

interface Props {
  jobId: string;
  s3Key: string;
}

export default function JobCard({ jobId, s3Key }: Props) {
  const [job, setJob] = useState<JobStatusResponse>({
    job_id: jobId,
    s3_key: s3Key,
    status: "pending",
    message: "Queued.",
    chunks_upserted: 0,
  });

  useEffect(() => {
    // Stop polling once the job reaches a terminal state
    if (job.status === "completed" || job.status === "failed") return;

    const interval = setInterval(() => {
      api
        .getJob(jobId)
        .then(setJob)
        .catch(() => {
          /* silently retry */
        });
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [jobId, job.status]);

  const style = STATUS_STYLES[job.status];

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
      {/* Header row */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-zinc-800 dark:text-zinc-100">
            {job.s3_key}
          </p>
          <p className="mt-0.5 font-mono text-xs text-zinc-400">{jobId}</p>
        </div>

        <span
          className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${style.pill}`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
          {style.label}
        </span>
      </div>

      {/* Message */}
      <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
        {job.message}
      </p>

      {/* Chunks upserted */}
      {job.status === "completed" && job.chunks_upserted > 0 && (
        <p className="mt-2 text-xs font-medium text-green-600">
          {job.chunks_upserted.toLocaleString()} vectors upserted to Pinecone
        </p>
      )}

      {/* Progress bar for running state */}
      {job.status === "running" && (
        <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-700">
          <div className="h-full w-1/2 animate-[shimmer_1.5s_ease-in-out_infinite] rounded-full bg-blue-400" />
        </div>
      )}
    </div>
  );
}
