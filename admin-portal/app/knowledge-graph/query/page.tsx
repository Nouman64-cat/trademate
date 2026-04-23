'use client';

/**
 * Knowledge Graph Query Explorer
 *
 * Search and explore HS codes with all related data
 */

import * as React from 'react';
import { DashboardLayout } from '../../components/dashboard-layout';
import { Search, Loader2, FileText, DollarSign, ShieldCheck, FileCheck, AlertTriangle } from 'lucide-react';
import { cn } from '../../utils/cn';
import api from '../../services/api';

interface HSCodeDetail {
  code: string;
  description: string;
  source: string;
  full_label: string | null;
  tariffs: any[];
  exemptions: any[];
  procedures: any[];
  measures: any[];
  cess: any[];
  anti_dumping: any[];
}

export default function QueryPage() {
  const [hsCode, setHsCode] = React.useState('');
  const [source, setSource] = React.useState<'PK' | 'US'>('PK');
  const [searching, setSearching] = React.useState(false);
  const [result, setResult] = React.useState<HSCodeDetail | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!hsCode.trim()) {
      setError('Please enter an HS code');
      return;
    }

    try {
      setSearching(true);
      setError(null);
      setResult(null);

      const data = await api.get<HSCodeDetail>(
        `/v1/admin/knowledge-graph/query/${encodeURIComponent(hsCode)}?source=${source}`
      );

      setResult(data);
    } catch (err: any) {
      console.error('Failed to query HS code:', err);
      setError(err.message || 'HS code not found');
    } finally {
      setSearching(false);
    }
  };

  return (
    <DashboardLayout
      breadcrumbs={[
        { title: 'Dashboard', href: '/dashboard' },
        { title: 'Knowledge Graph', href: '/knowledge-graph' },
        { title: 'Query' },
      ]}
    >
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            HS Code Explorer
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Search and explore HS codes with all related tariffs, exemptions, and procedures
          </p>
        </div>

        {/* Search Form */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* HS Code Input */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  HS Code
                </label>
                <input
                  type="text"
                  value={hsCode}
                  onChange={(e) => setHsCode(e.target.value)}
                  placeholder="e.g., 010121000000 (PK) or 0101.21 (US)"
                  className={cn(
                    'w-full px-4 py-2 rounded-lg border',
                    'bg-white dark:bg-gray-900',
                    'border-gray-200 dark:border-gray-700',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600',
                    'font-mono'
                  )}
                />
              </div>

              {/* Source Selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Source
                </label>
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value as 'PK' | 'US')}
                  className={cn(
                    'w-full px-4 py-2 rounded-lg border',
                    'bg-white dark:bg-gray-900',
                    'border-gray-200 dark:border-gray-700',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600'
                  )}
                >
                  <option value="PK">Pakistan (PCT)</option>
                  <option value="US">United States (HTS)</option>
                </select>
              </div>
            </div>

            {/* Search Button */}
            <button
              type="submit"
              disabled={searching}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {searching ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  Search HS Code
                </>
              )}
            </button>
          </form>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Basic Info */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <FileText className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 font-mono">
                      {result.code}
                    </h2>
                    <span className="px-2.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-sm font-medium">
                      {result.source}
                    </span>
                  </div>
                  <p className="mt-2 text-gray-700 dark:text-gray-300">
                    {result.description}
                  </p>
                  {result.full_label && (
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                      {result.full_label}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Tariffs */}
            {result.tariffs.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-4">
                  <DollarSign className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Tariffs ({result.tariffs.length})
                  </h3>
                </div>
                <div className="space-y-3">
                  {result.tariffs.map((tariff, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-gray-100">
                            {tariff.duty_name} ({tariff.duty_type})
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            Rate: {tariff.rate}
                          </p>
                        </div>
                        {(tariff.valid_from || tariff.valid_to) && (
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {tariff.valid_from && `From: ${tariff.valid_from}`}
                            {tariff.valid_to && ` To: ${tariff.valid_to}`}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Exemptions */}
            {result.exemptions.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-4">
                  <ShieldCheck className="h-5 w-5 text-green-600 dark:text-green-400" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Exemptions ({result.exemptions.length})
                  </h3>
                </div>
                <div className="space-y-3">
                  {result.exemptions.map((exemption, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
                    >
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        {exemption.exemption_type}
                      </p>
                      {exemption.exemption_desc && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {exemption.exemption_desc}
                        </p>
                      )}
                      <div className="mt-2 flex flex-wrap gap-2 text-sm">
                        {exemption.activity && (
                          <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded">
                            {exemption.activity}
                          </span>
                        )}
                        {exemption.rate && (
                          <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
                            Rate: {exemption.rate}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Procedures */}
            {result.procedures.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-4">
                  <FileCheck className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Procedures ({result.procedures.length})
                  </h3>
                </div>
                <div className="space-y-3">
                  {result.procedures.map((procedure, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
                    >
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        {procedure.name}
                      </p>
                      {procedure.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {procedure.description}
                        </p>
                      )}
                      {procedure.category && (
                        <span className="inline-block mt-2 px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded text-sm">
                          {procedure.category}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Measures */}
            {result.measures.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-4">
                  <AlertTriangle className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Measures ({result.measures.length})
                  </h3>
                </div>
                <div className="space-y-3">
                  {result.measures.map((measure, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
                    >
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        {measure.name}
                      </p>
                      {measure.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {measure.description}
                        </p>
                      )}
                      <div className="mt-2 flex flex-wrap gap-2 text-sm">
                        {measure.type && (
                          <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded">
                            {measure.type}
                          </span>
                        )}
                        {measure.agency && (
                          <span className="px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                            {measure.agency}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty State */}
            {result.tariffs.length === 0 &&
              result.exemptions.length === 0 &&
              result.procedures.length === 0 &&
              result.measures.length === 0 && (
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-8 text-center border border-gray-200 dark:border-gray-700">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600 dark:text-gray-400">
                    No additional data found for this HS code
                  </p>
                </div>
              )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
