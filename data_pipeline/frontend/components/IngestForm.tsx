"use client";

import { useRef, useState, useTransition } from "react";
import { api } from "@/lib/api";

interface SubmittedJob {
  jobId: string;
  s3Key: string;
}

interface Props {
  onJobSubmitted: (job: SubmittedJob) => void;
}

const SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".pptx", ".txt"];
const ACCEPT = SUPPORTED_EXTENSIONS.join(",");

type UploadStage = "idle" | "uploading" | "ingesting";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function IngestForm({ onJobSubmitted }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stage, setStage] = useState<UploadStage>("idle");
  const [isPending, startTransition] = useTransition();

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    setError(null);

    if (!file) {
      setSelectedFile(null);
      return;
    }

    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!SUPPORTED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported file type "${ext}". Supported: ${SUPPORTED_EXTENSIONS.join(", ")}`);
      setSelectedFile(null);
      // Reset the input so the same file can be re-selected after fixing the error
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    setSelectedFile(file);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFile) return;

    setError(null);

    startTransition(async () => {
      try {
        // Step 1 — upload local file → S3
        setStage("uploading");
        const { s3_key } = await api.uploadFile(selectedFile);

        // Step 2 — trigger ingestion pipeline
        setStage("ingesting");
        const res = await api.ingest(s3_key);

        onJobSubmitted({ jobId: res.job_id, s3Key: s3_key });

        // Reset form
        setSelectedFile(null);
        if (inputRef.current) inputRef.current.value = "";
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unexpected error.");
      } finally {
        setStage("idle");
      }
    });
  }

  const isSubmitting = isPending || stage !== "idle";

  const stageLabel: Record<UploadStage, string> = {
    idle: "Upload & Ingest",
    uploading: "Uploading to S3…",
    ingesting: "Queuing ingestion…",
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {/* Drop zone / file picker */}
      <div
        onClick={() => !isSubmitting && inputRef.current?.click()}
        className={`relative flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-8 text-center transition
          ${isSubmitting ? "cursor-not-allowed opacity-60" : "hover:border-blue-400 hover:bg-blue-50/50 dark:hover:bg-blue-950/20"}
          ${selectedFile ? "border-blue-400 bg-blue-50/40 dark:bg-blue-950/20" : "border-zinc-300 bg-white dark:border-zinc-700 dark:bg-zinc-900"}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          disabled={isSubmitting}
          onChange={handleFileChange}
          className="sr-only"
        />

        {selectedFile ? (
          <>
            <FileIcon className="h-8 w-8 text-blue-500" />
            <div>
              <p className="text-sm font-medium text-zinc-800 dark:text-zinc-100">
                {selectedFile.name}
              </p>
              <p className="text-xs text-zinc-500">{formatBytes(selectedFile.size)}</p>
            </div>
            {!isSubmitting && (
              <p className="text-xs text-blue-500">Click to choose a different file</p>
            )}
          </>
        ) : (
          <>
            <UploadIcon className="h-8 w-8 text-zinc-400" />
            <div>
              <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Click to select a file
              </p>
              <p className="text-xs text-zinc-400">
                {SUPPORTED_EXTENSIONS.join(", ")} — max 50 MB
              </p>
            </div>
          </>
        )}
      </div>

      {/* Error */}
      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600 dark:border-red-800 dark:bg-red-950 dark:text-red-400">
          {error}
        </p>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={isSubmitting || !selectedFile}
        className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSubmitting && (
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
        )}
        {stageLabel[stage]}
      </button>
    </form>
  );
}

// ── Inline SVG icons (no extra dependency) ───────────────────────────────────

function UploadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
    </svg>
  );
}

function FileIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  );
}
