'use client';

/**
 * Knowledge Graph Dashboard
 *
 * Overview of Memgraph ingestion status, statistics, and health
 */

import * as React from 'react';
import { DashboardLayout } from '../components/dashboard-layout';
import { Database, GitBranch, FileText, AlertCircle, CheckCircle, Activity } from 'lucide-react';
import { cn } from '../utils/cn';
import api from '../services/api';
import Link from 'next/link';

interface HealthStatus {
  status: string;
  message: string;
  connection_uri: string;
}

interface GraphStats {
  total_nodes: number;
  total_relationships: number;
  pk_hs_codes: number;
  us_hs_codes: number;
  tariffs: number;
  exemptions: number;
  procedures: number;
  measures: number;
  cess: number;
  anti_dumping: number;
}

export default function KnowledgeGraphPage() {
  const [health, setHealth] = React.useState<HealthStatus | null>(null);
  const [stats, setStats] = React.useState<GraphStats | null>(null);
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
        api.get<HealthStatus>('/v1/admin/knowledge-graph/health'),
        api.get<GraphStats>('/v1/admin/knowledge-graph/stats'),
      ]);

      setHealth(healthData);
      setStats(statsData);
    } catch (err: any) {
      console.error('Failed to fetch knowledge graph data:', err);
      setError(err.message || 'Failed to load knowledge graph data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout
        breadcrumbs={[
          { title: 'Dashboard', href: '/dashboard' },
          { title: 'Knowledge Graph' },
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
        { title: 'Knowledge Graph' },
      ]}
    >
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Knowledge Graph
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Memgraph database for Pakistan PCT and US HTS data
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
                Database Health
              </h2>
              <div
                className={cn(
                  'inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium',
                  health.status === 'healthy'
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                    : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                )}
              >
                {health.status === 'healthy' ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <AlertCircle className="h-4 w-4" />
                )}
                {health.status === 'healthy' ? 'Connected' : 'Disconnected'}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <Activity className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                <span className="text-gray-600 dark:text-gray-400">URI:</span>
                <span className="text-gray-900 dark:text-gray-100 font-mono">
                  {health.connection_uri}
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {health.message}
              </p>
            </div>
          </div>
        )}

        {/* Statistics Grid */}
        {stats && (
          <>
            {/* Top-level Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Total Nodes</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                      {stats.total_nodes.toLocaleString()}
                    </p>
                  </div>
                  <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <Database className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Total Relationships
                    </p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                      {stats.total_relationships.toLocaleString()}
                    </p>
                  </div>
                  <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                    <GitBranch className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                  </div>
                </div>
              </div>
            </div>

            {/* HS Codes */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                HS Codes
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Pakistan (PCT)</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                      {stats.pk_hs_codes.toLocaleString()}
                    </p>
                  </div>
                  <FileText className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>

                <div className="flex items-center justify-between p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">United States (HTS)</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                      {stats.us_hs_codes.toLocaleString()}
                    </p>
                  </div>
                  <FileText className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
            </div>

            {/* Related Data */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Related Data
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {stats.tariffs.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Tariffs</p>
                </div>

                <div className="text-center p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {stats.exemptions.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Exemptions</p>
                </div>

                <div className="text-center p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {stats.procedures.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Procedures</p>
                </div>

                <div className="text-center p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {stats.measures.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Measures</p>
                </div>

                <div className="text-center p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {stats.cess.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Cess</p>
                </div>

                <div className="text-center p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {stats.anti_dumping.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Anti-Dumping</p>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Link
              href="/knowledge-graph/ingest"
              className="flex items-center gap-3 p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <Database className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  Manage Ingestion
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Trigger PK/US data ingestion
                </p>
              </div>
            </Link>

            <Link
              href="/knowledge-graph/query"
              className="flex items-center gap-3 p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <FileText className="h-5 w-5 text-green-600 dark:text-green-400" />
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  Query HS Codes
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Search and explore HS code data
                </p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
