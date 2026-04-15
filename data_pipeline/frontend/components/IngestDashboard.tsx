"use client";

import { useState } from "react";
import IngestForm from "./IngestForm";
import JobCard from "./JobCard";

interface Job {
  jobId: string;
  s3Key: string;
}

export default function IngestDashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);

  function handleJobSubmitted(job: Job) {
    setJobs((prev) => [job, ...prev]);
  }

  return (
    <div className="flex flex-col gap-8">
      {/* Upload card */}
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
        <h2 className="mb-1 text-base font-semibold text-zinc-800 dark:text-zinc-100">
          Ingest a Document
        </h2>
        <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
          Enter the S3 key of your document. It will be parsed, chunked,
          embedded, and upserted to Pinecone in the background.
        </p>
        <IngestForm onJobSubmitted={handleJobSubmitted} />
      </section>

      {/* Jobs list */}
      {jobs.length > 0 && (
        <section>
          <h2 className="mb-3 text-base font-semibold text-zinc-800 dark:text-zinc-100">
            Jobs{" "}
            <span className="ml-1 rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-normal text-zinc-500 dark:bg-zinc-700 dark:text-zinc-400">
              {jobs.length}
            </span>
          </h2>
          <div className="flex flex-col gap-3">
            {jobs.map((job) => (
              <JobCard key={job.jobId} jobId={job.jobId} s3Key={job.s3Key} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
