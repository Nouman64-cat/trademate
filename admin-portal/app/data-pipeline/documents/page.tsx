'use client';

/**
 * Document Ingestion Management
 *
 * Upload documents to S3 and trigger ingestion pipeline
 */

import * as React from 'react';
import { DashboardLayout } from '../../components/dashboard-layout';
import { FileText, Upload, Loader2, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';
import { cn } from '../../utils/cn';
import api from '../../services/api';

interface Job {
  job_id: string;
  s3_key: string;
  status: string;
  message?: string;
  started_at?: string;
  completed_at?: string;
  chunks_count?: number;
  vectors_upserted?: number;
  error?: string;
}

const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.txt'];

export default function DocumentsPage() {
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [uploading, setUploading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [jobs, setJobs] = React.useState<Job[]>([]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setError(null);

    if (!file) {
      setSelectedFile(null);
      return;
    }

    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!SUPPORTED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported file type "${ext}". Supported: ${SUPPORTED_EXTENSIONS.join(', ')}`);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setError(null);

      // Step 1: Upload to S3
      const formData = new FormData();
      formData.append('file', selectedFile);

      const uploadResponse = await fetch(`${api.baseURL}/v1/admin/data-pipeline/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${api.getAuthToken()}`,
        },
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error('Upload failed');
      }

      const { s3_key } = await uploadResponse.json();

      // Step 2: Trigger ingestion
      const ingestResponse = await fetch(
        `${api.baseURL}/v1/admin/data-pipeline/ingest?s3_key=${encodeURIComponent(s3_key)}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${api.getAuthToken()}`,
          },
        }
      );

      if (!ingestResponse.ok) {
        throw new Error('Ingestion trigger failed');
      }

      const { job_id, status, message } = await ingestResponse.json();

      // Add job to list and start polling
      const newJob: Job = {
        job_id,
        s3_key,
        status,
        message,
      };

      setJobs((prev) => [newJob, ...prev]);
      startPolling(job_id);

      // Reset form
      setSelectedFile(null);
    } catch (err: any) {
      console.error('Upload failed:', err);
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const startPolling = (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const jobStatus = await api.get<Job>(`/v1/admin/data-pipeline/job/${jobId}`);

        setJobs((prev) =>
          prev.map((job) => (job.job_id === jobId ? jobStatus : job))
        );

        // Stop polling if job is done
        if (jobStatus.status === 'completed' || jobStatus.status === 'failed') {
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Failed to poll job status:', err);
        clearInterval(interval);
      }
    }, 2000);

    // Clean up after 5 minutes
    setTimeout(() => clearInterval(interval), 5 * 60 * 1000);
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatTimestamp = (timestamp: string | undefined) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />;
      case 'processing':
        return <Loader2 className="h-5 w-5 text-blue-600 dark:text-blue-400 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />;
      default:
        return <Clock className="h-5 w-5 text-gray-600 dark:text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400';
      case 'processing':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400';
      case 'completed':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
      case 'failed':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400';
      default:
        return 'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-400';
    }
  };

  return (
    <DashboardLayout
      breadcrumbs={[
        { title: 'Dashboard', href: '/dashboard' },
        { title: 'Data Pipeline', href: '/data-pipeline' },
        { title: 'Documents' },
      ]}
    >
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Document Ingestion
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Upload and process documents for the RAG pipeline
          </p>
        </div>

        {/* Upload Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Upload Document
          </h2>

          {/* File Picker */}
          <div className="space-y-4">
            <div
              onClick={() => !uploading && document.getElementById('file-input')?.click()}
              className={cn(
                'relative flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-8 text-center transition',
                uploading
                  ? 'cursor-not-allowed opacity-60'
                  : 'hover:border-blue-400 hover:bg-blue-50/50 dark:hover:bg-blue-950/20',
                selectedFile
                  ? 'border-blue-400 bg-blue-50/40 dark:bg-blue-950/20'
                  : 'border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900'
              )}
            >
              <input
                id="file-input"
                type="file"
                accept={SUPPORTED_EXTENSIONS.join(',')}
                disabled={uploading}
                onChange={handleFileChange}
                className="sr-only"
              />

              {selectedFile ? (
                <>
                  <FileText className="h-8 w-8 text-blue-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-800 dark:text-gray-100">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-gray-500">{formatBytes(selectedFile.size)}</p>
                  </div>
                  {!uploading && (
                    <p className="text-xs text-blue-500">Click to choose a different file</p>
                  )}
                </>
              ) : (
                <>
                  <Upload className="h-8 w-8 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Click to select a file
                    </p>
                    <p className="text-xs text-gray-400">
                      {SUPPORTED_EXTENSIONS.join(', ')} — max 50 MB
                    </p>
                  </div>
                </>
              )}
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
                  <p className="text-red-800 dark:text-red-200">{error}</p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              onClick={handleUpload}
              disabled={uploading || !selectedFile}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Uploading & Ingesting...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  Upload & Ingest
                </>
              )}
            </button>
          </div>
        </div>

        {/* Jobs List */}
        {jobs.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Ingestion Jobs{' '}
              <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
                ({jobs.length})
              </span>
            </h2>

            <div className="space-y-3">
              {jobs.map((job) => (
                <div
                  key={job.job_id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      {getStatusIcon(job.status)}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 dark:text-gray-100 truncate">
                          {job.s3_key.split('/').pop()}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                          {job.s3_key}
                        </p>
                        {job.message && (
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            {job.message}
                          </p>
                        )}
                        {job.error && (
                          <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                            Error: {job.error}
                          </p>
                        )}
                      </div>
                    </div>
                    <span
                      className={cn(
                        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
                        getStatusColor(job.status)
                      )}
                    >
                      {job.status}
                    </span>
                  </div>

                  {/* Job Details */}
                  <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500 dark:text-gray-400">Started</p>
                      <p className="text-gray-900 dark:text-gray-100 font-medium">
                        {formatTimestamp(job.started_at)}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500 dark:text-gray-400">Completed</p>
                      <p className="text-gray-900 dark:text-gray-100 font-medium">
                        {formatTimestamp(job.completed_at)}
                      </p>
                    </div>
                    {job.chunks_count !== undefined && (
                      <div>
                        <p className="text-gray-500 dark:text-gray-400">Chunks</p>
                        <p className="text-gray-900 dark:text-gray-100 font-medium">
                          {job.chunks_count}
                        </p>
                      </div>
                    )}
                    {job.vectors_upserted !== undefined && (
                      <div>
                        <p className="text-gray-500 dark:text-gray-400">Vectors</p>
                        <p className="text-gray-900 dark:text-gray-100 font-medium">
                          {job.vectors_upserted}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
