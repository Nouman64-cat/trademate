'use client';

/**
 * Research Pipeline Management
 *
 * Trigger research runs for trade news, trends, and UN Comtrade data
 */

import * as React from 'react';
import { DashboardLayout } from '../../components/dashboard-layout';
import {  TrendingUp, Play, AlertCircle, Info } from 'lucide-react';
import { cn } from '../../utils/cn';

export default function ResearchPage() {
  const [query, setQuery] = React.useState('');
  const [maxItems, setMaxItems] = React.useState(20);
  const [fullFetchLimit, setFullFetchLimit] = React.useState(10);
  const [requireAll, setRequireAll] = React.useState(true);
  const [forceStatsRefresh, setForceStatsRefresh] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleTrigger = async () => {
    setError(null);

    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    // Note: Research pipeline trigger is not implemented yet
    // It requires Lambda integration or running the research service locally
    setError(
      'Research pipeline trigger requires Lambda integration. ' +
      'Use the data pipeline backend directly or deploy to AWS Lambda to trigger research runs.'
    );
  };

  return (
    <DashboardLayout
      breadcrumbs={[
        { title: 'Dashboard', href: '/dashboard' },
        { title: 'Data Pipeline', href: '/data-pipeline' },
        { title: 'Research' },
      ]}
    >
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Research Pipeline
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Fetch trade news, trends, and UN Comtrade statistics
          </p>
        </div>

        {/* Info Banner */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-blue-800 dark:text-blue-200 font-medium">
                About the Research Pipeline
              </p>
              <ul className="text-sm text-blue-700 dark:text-blue-300 mt-2 space-y-1 list-disc list-inside">
                <li>Fetches trade-related articles from curated RSS feeds</li>
                <li>Filters by keyword matching (AND/OR logic)</li>
                <li>Analyzes content with OpenAI for trade insights</li>
                <li>Generates embeddings and stores in Pinecone</li>
                <li>Optionally refreshes UN Comtrade bilateral trade statistics</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Trigger Form */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Trigger Research Run
          </h2>

          <div className="space-y-4">
            {/* Query Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search Query
              </label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., US Pakistan textile trade"
                className={cn(
                  'w-full px-4 py-2 rounded-lg border',
                  'bg-white dark:bg-gray-900',
                  'border-gray-200 dark:border-gray-700',
                  'focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600'
                )}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Keywords to filter news articles
              </p>
            </div>

            {/* Settings Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Max Items to Fetch
                </label>
                <input
                  type="number"
                  value={maxItems}
                  onChange={(e) => setMaxItems(parseInt(e.target.value) || 20)}
                  className={cn(
                    'w-full px-4 py-2 rounded-lg border',
                    'bg-white dark:bg-gray-900',
                    'border-gray-200 dark:border-gray-700',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600'
                  )}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Maximum articles to fetch per run
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Full Fetch Limit
                </label>
                <input
                  type="number"
                  value={fullFetchLimit}
                  onChange={(e) => setFullFetchLimit(parseInt(e.target.value) || 10)}
                  className={cn(
                    'w-full px-4 py-2 rounded-lg border',
                    'bg-white dark:bg-gray-900',
                    'border-gray-200 dark:border-gray-700',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600'
                  )}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  How many matched items to fetch full article content
                </p>
              </div>
            </div>

            {/* Checkboxes */}
            <div className="space-y-3">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={requireAll}
                  onChange={(e) => setRequireAll(e.target.checked)}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    Require All Keywords (AND logic)
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    If unchecked, uses OR logic (match any keyword)
                  </p>
                </div>
              </label>

              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={forceStatsRefresh}
                  onChange={(e) => setForceStatsRefresh(e.target.checked)}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    Force UN Comtrade Stats Refresh
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Fetch latest bilateral trade statistics (normally runs daily at 00:00 UTC)
                  </p>
                </div>
              </label>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              onClick={handleTrigger}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
            >
              <Play className="h-4 w-4" />
              Trigger Research Run
            </button>
          </div>
        </div>

        {/* Data Sources */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Data Sources
          </h2>

          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <h3 className="font-medium text-gray-900 dark:text-gray-100">
                1. News & Trends (RSS/Web)
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Fetches articles from curated RSS feeds, filters by keywords, and extracts full
                article text using OpenAI for summarization.
              </p>
            </div>

            <div className="border-l-4 border-green-500 pl-4">
              <h3 className="font-medium text-gray-900 dark:text-gray-100">
                2. Trade Statistics (UN Comtrade)
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Fetches official bilateral trade data between the US and Pakistan using the UN
                Comtrade Public API. Converts numeric records into descriptive text for RAG
                analysis.
              </p>
            </div>
          </div>
        </div>

        {/* Automated Schedule */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Automated Updates
          </h2>

          <div className="space-y-3">
            <div className="flex items-start gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex-shrink-0 w-20 text-sm font-medium text-blue-700 dark:text-blue-400">
                Hourly
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                Fetches latest news, trends, and market sentiment from RSS feeds
              </p>
            </div>

            <div className="flex items-start gap-3 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex-shrink-0 w-20 text-sm font-medium text-green-700 dark:text-green-400">
                Daily
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                Triggers Trade Stats Refresh for UN Comtrade data at 00:00 UTC. Since official
                stats change less frequently, this saves on API and embedding costs.
              </p>
            </div>

            <div className="flex items-start gap-3 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <div className="flex-shrink-0 w-20 text-sm font-medium text-purple-700 dark:text-purple-400">
                Manual
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                Force a stats update at any time using the form above with "Force UN Comtrade
                Stats Refresh" enabled
              </p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
