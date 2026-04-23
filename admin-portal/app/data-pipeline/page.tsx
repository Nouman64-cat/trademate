'use client';

/**
 * Data Pipeline Dashboard
 *
 * Overview of document ingestion, research pipeline, and vector store status
 */

import * as React from 'react';
import { DashboardLayout } from '../components/dashboard-layout';
import { Database, FileText, TrendingUp, Activity, AlertCircle, CheckCircle, Clock, Upload } from 'lucide-react';
import { cn } from '../utils/cn';
import api from '../services/api';
import Link from 'next/link';

interface HealthStatus {
  status: string;
  services: {
    [key: string]: string;
  };
}

interface PipelineStats {
  total_documents_ingested: number;
  total_vectors_in_pinecone: number;
  total_research_runs: number;
  last_ingestion_time: string | null;
  last_research_time: string | null;
  s3_storage_used_bytes: number | null;
}

export default function DataPipelinePage() {
  const [health, setHealth] = React.useState<HealthStatus | null>(null);
  const [stats, setStats] = React.useState<PipelineStats | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [healthData, statsData] = await Promise.all([
        api.get<HealthStatus>('/v1/admin/data-pipeline/health'),
        api.get<PipelineStats>('/v1/admin/data-pipeline/stats'),
      ]);

      setHealth(healthData);
      setStats(statsData);
    } catch (err: any) {
      console.error('Failed to fetch pipeline data:', err);
      setError(err.message || 'Failed to load pipeline data');
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number | null) => {
    if (bytes === null) return 'N/A';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'Never';
    return new Date(timestamp).toLocaleString();
  };

  if (loading) {
    return (
      <DashboardLayout
        breadcrumbs={[
          { title: 'Dashboard', href: '/dashboard' },
          { title: 'Data Pipeline' },
        ]}
      >
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      breadcrumbs={[
        { title: 'Dashboard', href: '/dashboard' },
        { title: 'Data Pipeline' },
      ]}
    >
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Data Pipeline
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Document ingestion, research pipeline, and vector store management
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
              <p className="text-red-800 dark:text-red-200">{error}</p>
            </div>
            <button
              onClick={fetchData}
              className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
            >
              Try again
            </button>
          </div>
        )}

        {/* Health Status */}
        {health && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                System Health
              </h2>
              <div
                className={cn(
                  'inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium',
                  health.status === 'healthy'
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                    : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                )}
              >
                {health.status === 'healthy' ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <AlertCircle className="h-4 w-4" />
                )}
                {health.status === 'healthy' ? 'All Systems Operational' : 'Degraded'}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(health.services).map(([service, status]) => (
                <div
                  key={service}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        'p-2 rounded-lg',
                        status === 'ok'
                          ? 'bg-green-100 dark:bg-green-900/30'
                          : 'bg-red-100 dark:bg-red-900/30'
                      )}
                    >
                      {service === 'pinecone' && <Database className="h-5 w-5 text-green-600 dark:text-green-400" />}
                      {service === 's3' && <Upload className="h-5 w-5 text-green-600 dark:text-green-400" />}
                      {service === 'openai' && <Activity className="h-5 w-5 text-green-600 dark:text-green-400" />}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100 capitalize">
                        {service}
                      </p>
                      <p
                        className={cn(
                          'text-sm',
                          status === 'ok'
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-red-600 dark:text-red-400'
                        )}
                      >
                        {status}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Documents Ingested</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                    {stats.total_documents_ingested.toLocaleString()}
                  </p>
                </div>
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <FileText className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Last: {formatTimestamp(stats.last_ingestion_time)}
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Vectors in Pinecone</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                    {stats.total_vectors_in_pinecone.toLocaleString()}
                  </p>
                </div>
                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <Database className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Searchable embeddings
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Research Runs</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                    {stats.total_research_runs.toLocaleString()}
                  </p>
                </div>
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <TrendingUp className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Last: {formatTimestamp(stats.last_research_time)}
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 md:col-span-2 lg:col-span-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">S3 Storage Used</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                    {formatBytes(stats.s3_storage_used_bytes)}
                  </p>
                </div>
                <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                  <Upload className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                </div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Documents and research results stored in S3
              </p>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Link
              href="/data-pipeline/documents"
              className="flex items-center gap-3 p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  Manage Documents
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Upload and ingest documents
                </p>
              </div>
            </Link>

            <Link
              href="/data-pipeline/research"
              className="flex items-center gap-3 p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <TrendingUp className="h-5 w-5 text-green-600 dark:text-green-400" />
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  Research Pipeline
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Trigger news & trade data research
                </p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
