'use client';

/**
 * Knowledge Graph Ingestion Control
 *
 * Trigger and monitor Pakistan PCT and US HTS data ingestion
 */

import * as React from 'react';
import { DashboardLayout } from '../../components/dashboard-layout';
import { Play, Clock, CheckCircle, XCircle, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '../../utils/cn';
import api from '../../services/api';

interface IngestionJob {
  job_id: string;
  source: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  message: string | null;
  logs: string[];
}

export default function IngestionPage() {
  const [jobs, setJobs] = React.useState<IngestionJob[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [triggering, setTriggering] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [expandedJobs, setExpandedJobs] = React.useState<Set<string>>(new Set());

  React.useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      setError(null);
      const data = await api.get<IngestionJob[]>('/v1/admin/knowledge-graph/jobs');
      setJobs(data);
    } catch (err: any) {
      console.error('Failed to fetch jobs:', err);
      setError(err.message || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  const triggerIngestion = async (source: 'PK' | 'US') => {
    try {
      setTriggering(source);
      setError(null);

      const endpoint =
        source === 'PK'
          ? '/v1/admin/knowledge-graph/ingest/pk'
          : '/v1/admin/knowledge-graph/ingest/us';

      await api.post(endpoint, {});

      // Refresh jobs list
      await fetchJobs();
    } catch (err: any) {
      console.error(`Failed to trigger ${source} ingestion:`, err);
      setError(err.message || `Failed to trigger ${source} ingestion`);
    } finally {
      setTriggering(null);
    }
  };

  const toggleJobExpansion = (jobId: string) => {
    setExpandedJobs((prev) => {
      const next = new Set(prev);
      if (next.has(jobId)) {
        next.delete(jobId);
      } else {
        next.add(jobId);
      }
      return next;
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
      case 'running':
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
      case 'running':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400';
      case 'completed':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
      case 'failed':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400';
      default:
        return 'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-400';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const isRunning = (source: string) => {
    return jobs.some((job) => job.source === source && job.status === 'running');
  };

  return (
    <DashboardLayout
      breadcrumbs={[
        { title: 'Dashboard', href: '/dashboard' },
        { title: 'Knowledge Graph', href: '/knowledge-graph' },
        { title: 'Ingestion' },
      ]}
    >
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Data Ingestion
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Trigger and monitor Pakistan PCT and US HTS data ingestion
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Trigger Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Pakistan Ingestion */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Pakistan PCT Data
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Ingest Pakistan Customs Tariff hierarchy, tariffs, exemptions, cess,
              anti-dumping duties, procedures, and measures.
            </p>
            <button
              onClick={() => triggerIngestion('PK')}
              disabled={triggering !== null || isRunning('PK')}
              className={cn(
                'w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors',
                isRunning('PK')
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 cursor-not-allowed'
                  : 'bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {triggering === 'PK' || isRunning('PK') ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {isRunning('PK') ? 'Running...' : 'Starting...'}
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Trigger PK Ingestion
                </>
              )}
            </button>
          </div>

          {/* US Ingestion */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              US HTS Data
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Ingest United States Harmonized Tariff Schedule hierarchy and related
              trade data.
            </p>
            <button
              onClick={() => triggerIngestion('US')}
              disabled={triggering !== null || isRunning('US')}
              className={cn(
                'w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors',
                isRunning('US')
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {triggering === 'US' || isRunning('US') ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {isRunning('US') ? 'Running...' : 'Starting...'}
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Trigger US Ingestion
                </>
              )}
            </button>
          </div>
        </div>

        {/* Jobs List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Ingestion Jobs{' '}
            {jobs.length > 0 && (
              <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
                ({jobs.length})
              </span>
            )}
          </h2>

          {loading ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
            </div>
          ) : jobs.length === 0 ? (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">
              No ingestion jobs yet. Trigger an ingestion to get started.
            </p>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => (
                <div
                  key={job.job_id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  {/* Job Header */}
                  <div className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        {getStatusIcon(job.status)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-gray-900 dark:text-gray-100">
                              {job.source === 'PK' ? 'Pakistan PCT' : 'US HTS'} Ingestion
                            </p>
                            <span
                              className={cn(
                                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                                getStatusColor(job.status)
                              )}
                            >
                              {job.status}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            ID: {job.job_id}
                          </p>
                          {job.message && (
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                              {job.message}
                            </p>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => toggleJobExpansion(job.job_id)}
                        className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                      >
                        {expandedJobs.has(job.job_id) ? (
                          <ChevronUp className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                        ) : (
                          <ChevronDown className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                        )}
                      </button>
                    </div>

                    {/* Timestamps */}
                    <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500 dark:text-gray-400">Started</p>
                        <p className="text-gray-900 dark:text-gray-100 font-medium">
                          {formatTimestamp(job.started_at)}
                        </p>
                      </div>
                      {job.completed_at && (
                        <div>
                          <p className="text-gray-500 dark:text-gray-400">Completed</p>
                          <p className="text-gray-900 dark:text-gray-100 font-medium">
                            {formatTimestamp(job.completed_at)}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Logs (expanded) */}
                  {expandedJobs.has(job.job_id) && job.logs.length > 0 && (
                    <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-900">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Logs (last {job.logs.length} lines):
                      </p>
                      <div className="bg-black rounded-lg p-3 overflow-auto max-h-64">
                        <pre className="text-xs text-green-400 font-mono">
                          {job.logs.join('\n')}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
