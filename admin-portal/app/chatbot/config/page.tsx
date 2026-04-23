'use client';

/**
 * Chatbot Configuration Page
 *
 * Manage chatbot settings, LLM parameters, tools, and features
 */

import * as React from 'react';
import { DashboardLayout } from '../../components/dashboard-layout';
import { Save, RefreshCw, Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { ChatbotSettings } from '../../types';
import api from '../../services/api';

export default function ChatbotConfigPage() {
  const [config, setConfig] = React.useState<ChatbotSettings | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.get<ChatbotSettings>('/v1/admin/chatbot/config');
      setConfig(data);
    } catch (err: any) {
      console.error('Failed to fetch chatbot config:', err);
      setError(err.message || 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!config) return;

    try {
      setSaving(true);
      setError(null);
      await api.put('/v1/admin/chatbot/config', config);
      alert('Configuration saved successfully!');
    } catch (err: any) {
      console.error('Failed to save chatbot config:', err);
      setError(err.message || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset to default values?')) {
      fetchConfig(); // Reload from server
    }
  };

  if (loading) {
    return (
      <DashboardLayout
        breadcrumbs={[
          { title: 'Dashboard', href: '/dashboard' },
          { title: 'Chatbot', href: '/chatbot' },
          { title: 'Configuration' },
        ]}
      >
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      </DashboardLayout>
    );
  }

  if (error || !config) {
    return (
      <DashboardLayout
        breadcrumbs={[
          { title: 'Dashboard', href: '/dashboard' },
          { title: 'Chatbot', href: '/chatbot' },
          { title: 'Configuration' },
        ]}
      >
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">Error: {error}</p>
          <button
            onClick={fetchConfig}
            className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
          >
            Try again
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      breadcrumbs={[
        { title: 'Dashboard', href: '/dashboard' },
        { title: 'Chatbot', href: '/chatbot' },
        { title: 'Configuration' },
      ]}
    >
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Chatbot Configuration
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Configure LLM parameters, tools, and feature flags
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleReset}
              className="inline-flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Reset
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="h-4 w-4" />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>

        {/* Configuration Sections */}
        <div className="space-y-6">
          {/* LLM Settings */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              LLM Settings
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Model
                </label>
                <select
                  value={config.llm_model}
                  onChange={(e) =>
                    setConfig({ ...config, llm_model: e.target.value })
                  }
                  className={cn(
                    'w-full px-4 py-2 rounded-lg border',
                    'bg-white dark:bg-gray-900',
                    'border-gray-200 dark:border-gray-700',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600'
                  )}
                >
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-4o-mini">GPT-4o Mini</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Temperature: {config.temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={config.temperature}
                  onChange={(e) =>
                    setConfig({ ...config, temperature: parseFloat(e.target.value) })
                  }
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                  <span>Precise</span>
                  <span>Creative</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Max Tokens
                </label>
                <input
                  type="number"
                  value={config.max_tokens}
                  onChange={(e) =>
                    setConfig({ ...config, max_tokens: parseInt(e.target.value) })
                  }
                  className={cn(
                    'w-full px-4 py-2 rounded-lg border',
                    'bg-white dark:bg-gray-900',
                    'border-gray-200 dark:border-gray-700',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600'
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Top P: {config.top_p}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.top_p}
                  onChange={(e) =>
                    setConfig({ ...config, top_p: parseFloat(e.target.value) })
                  }
                  className="w-full"
                />
              </div>
            </div>
          </div>

          {/* Agent Settings */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Agent Settings
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    Router Enabled
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Allow agent to intelligently select tools
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.router_enabled}
                    onChange={(e) =>
                      setConfig({ ...config, router_enabled: e.target.checked })
                    }
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Max Tool Calls per Message
                </label>
                <input
                  type="number"
                  value={config.max_tool_calls}
                  onChange={(e) =>
                    setConfig({ ...config, max_tool_calls: parseInt(e.target.value) })
                  }
                  className={cn(
                    'w-full px-4 py-2 rounded-lg border',
                    'bg-white dark:bg-gray-900',
                    'border-gray-200 dark:border-gray-700',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600'
                  )}
                />
              </div>
            </div>
          </div>

          {/* Rate Limiting */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Rate Limiting
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Max Messages per Hour
                </label>
                <input
                  type="number"
                  value={config.max_messages_per_hour}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      max_messages_per_hour: parseInt(e.target.value),
                    })
                  }
                  className={cn(
                    'w-full px-4 py-2 rounded-lg border',
                    'bg-white dark:bg-gray-900',
                    'border-gray-200 dark:border-gray-700',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600'
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Max Conversations per Day
                </label>
                <input
                  type="number"
                  value={config.max_conversations_per_day}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      max_conversations_per_day: parseInt(e.target.value),
                    })
                  }
                  className={cn(
                    'w-full px-4 py-2 rounded-lg border',
                    'bg-white dark:bg-gray-900',
                    'border-gray-200 dark:border-gray-700',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600'
                  )}
                />
              </div>
            </div>
          </div>

          {/* Features */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Features
            </h2>
            <div className="space-y-4">
              {[
                {
                  key: 'document_search_enabled',
                  label: 'Document Search',
                  description: 'Enable PDF document search via Pinecone',
                },
                {
                  key: 'route_evaluation_enabled',
                  label: 'Route Evaluation',
                  description: 'Enable shipping route comparison tool',
                },
                {
                  key: 'hs_code_search_enabled',
                  label: 'HS Code Search',
                  description: 'Enable HS code lookup via Memgraph',
                },
                {
                  key: 'recommendation_enabled',
                  label: 'Recommendations',
                  description: 'Enable ML-powered recommendations',
                },
                {
                  key: 'interaction_tracking_enabled',
                  label: 'Interaction Tracking',
                  description: 'Track user interactions for analytics',
                },
              ].map((feature) => (
                <div key={feature.key} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-gray-100">
                      {feature.label}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {feature.description}
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config[feature.key as keyof ChatbotSettings] as boolean}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          [feature.key]: e.target.checked,
                        })
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
