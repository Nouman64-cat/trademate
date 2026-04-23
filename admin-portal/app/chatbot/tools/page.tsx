'use client';

/**
 * Chatbot Tools Page
 *
 * Manage available tools and their configurations for the chatbot agent
 */

import * as React from 'react';
import { DashboardLayout } from '../../components/dashboard-layout';
import {
  Database,
  FileText,
  Navigation,
  Search,
  CheckCircle,
  XCircle,
  Settings,
  Code,
  Globe,
  Lightbulb,
  Save,
  RefreshCw,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { cn } from '../../utils/cn';

interface Tool {
  id: string;
  name: string;
  description: string;
  category: 'search' | 'analysis' | 'recommendation' | 'data';
  enabled: boolean;
  icon: any;
  parameters?: {
    name: string;
    type: string;
    required: boolean;
    description: string;
    default?: any;
  }[];
  apiEndpoint?: string;
  performance?: {
    avgResponseTime: number;
    successRate: number;
    usageCount: number;
  };
}

export default function ChatbotToolsPage() {
  const [tools, setTools] = React.useState<Tool[]>([
    {
      id: 'search_pakistan_hs_data',
      name: 'Search Pakistan HS Data',
      description: 'Search and retrieve HS codes, tariffs, and trade data from Pakistan Customs',
      category: 'search',
      enabled: true,
      icon: Database,
      apiEndpoint: 'Memgraph Vector Search',
      parameters: [
        {
          name: 'query',
          type: 'string',
          required: true,
          description: 'Natural language search query',
        },
        {
          name: 'top_k',
          type: 'integer',
          required: false,
          description: 'Number of results to return',
          default: 5,
        },
      ],
      performance: {
        avgResponseTime: 1250,
        successRate: 98.5,
        usageCount: 15420,
      },
    },
    {
      id: 'search_us_hs_data',
      name: 'Search US HS Data',
      description: 'Search and retrieve HS codes and tariff data from US Customs',
      category: 'search',
      enabled: true,
      icon: Globe,
      apiEndpoint: 'Memgraph Vector Search',
      parameters: [
        {
          name: 'query',
          type: 'string',
          required: true,
          description: 'Natural language search query',
        },
        {
          name: 'top_k',
          type: 'integer',
          required: false,
          description: 'Number of results to return',
          default: 5,
        },
      ],
      performance: {
        avgResponseTime: 1180,
        successRate: 97.8,
        usageCount: 8930,
      },
    },
    {
      id: 'search_trade_documents',
      name: 'Search Trade Documents',
      description: 'Semantic search across uploaded trade documents, policies, and regulations',
      category: 'search',
      enabled: true,
      icon: FileText,
      apiEndpoint: 'Pinecone Vector DB',
      parameters: [
        {
          name: 'query',
          type: 'string',
          required: true,
          description: 'Search query',
        },
        {
          name: 'top_k',
          type: 'integer',
          required: false,
          description: 'Number of documents to return',
          default: 3,
        },
      ],
      performance: {
        avgResponseTime: 850,
        successRate: 99.2,
        usageCount: 12560,
      },
    },
    {
      id: 'evaluate_shipping_routes',
      name: 'Evaluate Shipping Routes',
      description: 'Compare and analyze shipping routes with cost and time estimates',
      category: 'analysis',
      enabled: true,
      icon: Navigation,
      apiEndpoint: 'Route Engine API',
      parameters: [
        {
          name: 'origin_city',
          type: 'string',
          required: true,
          description: 'Origin city name',
        },
        {
          name: 'destination_city',
          type: 'string',
          required: true,
          description: 'Destination city name',
        },
        {
          name: 'cargo_type',
          type: 'string',
          required: true,
          description: 'Type of cargo',
        },
        {
          name: 'cargo_value_usd',
          type: 'number',
          required: false,
          description: 'Value of cargo in USD',
        },
      ],
      performance: {
        avgResponseTime: 2100,
        successRate: 96.3,
        usageCount: 5240,
      },
    },
    {
      id: 'recommend_hs_codes',
      name: 'Recommend HS Codes',
      description: 'ML-powered recommendations for related HS codes based on user context',
      category: 'recommendation',
      enabled: true,
      icon: Lightbulb,
      apiEndpoint: 'Recommendation Service',
      parameters: [
        {
          name: 'context_codes',
          type: 'array',
          required: true,
          description: 'Recently searched HS codes',
        },
        {
          name: 'top_k',
          type: 'integer',
          required: false,
          description: 'Number of recommendations',
          default: 10,
        },
      ],
      performance: {
        avgResponseTime: 450,
        successRate: 94.7,
        usageCount: 3820,
      },
    },
    {
      id: 'recommend_documents',
      name: 'Recommend Documents',
      description: 'Context-aware document recommendations based on conversation history',
      category: 'recommendation',
      enabled: true,
      icon: FileText,
      apiEndpoint: 'Recommendation Service',
      parameters: [
        {
          name: 'conversation_context',
          type: 'array',
          required: true,
          description: 'Recent messages',
        },
        {
          name: 'top_k',
          type: 'integer',
          required: false,
          description: 'Number of recommendations',
          default: 3,
        },
      ],
      performance: {
        avgResponseTime: 680,
        successRate: 91.2,
        usageCount: 2140,
      },
    },
    {
      id: 'optimize_tariff',
      name: 'Tariff Optimization',
      description: 'Find alternative HS classifications with lower duty rates',
      category: 'analysis',
      enabled: true,
      icon: Search,
      apiEndpoint: 'Tariff Optimizer',
      parameters: [
        {
          name: 'hs_code',
          type: 'string',
          required: true,
          description: 'Current HS code',
        },
        {
          name: 'cargo_value_usd',
          type: 'number',
          required: true,
          description: 'Cargo value for savings calculation',
        },
        {
          name: 'source',
          type: 'string',
          required: false,
          description: 'PK or US',
          default: 'PK',
        },
      ],
      performance: {
        avgResponseTime: 920,
        successRate: 89.5,
        usageCount: 1680,
      },
    },
  ]);

  const [expandedTools, setExpandedTools] = React.useState<Set<string>>(new Set());
  const [saving, setSaving] = React.useState(false);
  const [filter, setFilter] = React.useState<'all' | 'search' | 'analysis' | 'recommendation' | 'data'>('all');

  const toggleTool = (toolId: string) => {
    setTools(tools.map(tool =>
      tool.id === toolId ? { ...tool, enabled: !tool.enabled } : tool
    ));
  };

  const toggleExpanded = (toolId: string) => {
    const newExpanded = new Set(expandedTools);
    if (newExpanded.has(toolId)) {
      newExpanded.delete(toolId);
    } else {
      newExpanded.add(toolId);
    }
    setExpandedTools(newExpanded);
  };

  const handleSave = async () => {
    setSaving(true);
    // TODO: Save to API
    setTimeout(() => {
      setSaving(false);
      alert('Tool configuration saved successfully!');
    }, 1000);
  };

  const handleReset = () => {
    if (confirm('Reset all tools to default configuration?')) {
      window.location.reload();
    }
  };

  const filteredTools = filter === 'all'
    ? tools
    : tools.filter(tool => tool.category === filter);

  const enabledCount = tools.filter(t => t.enabled).length;
  const totalUsage = tools.reduce((sum, t) => sum + (t.performance?.usageCount || 0), 0);
  const avgSuccessRate = tools.reduce((sum, t) => sum + (t.performance?.successRate || 0), 0) / tools.length;

  return (
    <DashboardLayout
      breadcrumbs={[
        { title: 'Dashboard', href: '/dashboard' },
        { title: 'Chatbot', href: '/chatbot' },
        { title: 'Tools' },
      ]}
    >
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Chatbot Tools
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Manage available tools and configurations for the AI agent
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
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <Settings className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Tools</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{tools.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <CheckCircle className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Enabled</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{enabledCount}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                <Code className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Calls</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {totalUsage.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/20 rounded-lg">
                <CheckCircle className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Success Rate</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {avgSuccessRate.toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Filter:</span>
            {(['all', 'search', 'analysis', 'recommendation', 'data'] as const).map((category) => (
              <button
                key={category}
                onClick={() => setFilter(category)}
                className={cn(
                  'px-3 py-1.5 text-sm rounded-lg transition-colors',
                  filter === category
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                )}
              >
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Tools List */}
        <div className="space-y-4">
          {filteredTools.map((tool) => {
            const Icon = tool.icon;
            const isExpanded = expandedTools.has(tool.id);

            return (
              <div
                key={tool.id}
                className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
              >
                {/* Tool Header */}
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className={cn(
                        'p-3 rounded-lg',
                        tool.category === 'search' && 'bg-blue-100 dark:bg-blue-900/20',
                        tool.category === 'analysis' && 'bg-purple-100 dark:bg-purple-900/20',
                        tool.category === 'recommendation' && 'bg-green-100 dark:bg-green-900/20',
                        tool.category === 'data' && 'bg-orange-100 dark:bg-orange-900/20'
                      )}>
                        <Icon className={cn(
                          'h-6 w-6',
                          tool.category === 'search' && 'text-blue-600',
                          tool.category === 'analysis' && 'text-purple-600',
                          tool.category === 'recommendation' && 'text-green-600',
                          tool.category === 'data' && 'text-orange-600'
                        )} />
                      </div>

                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                            {tool.name}
                          </h3>
                          <span className={cn(
                            'px-2 py-0.5 text-xs font-medium rounded-full',
                            tool.category === 'search' && 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
                            tool.category === 'analysis' && 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
                            tool.category === 'recommendation' && 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
                            tool.category === 'data' && 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
                          )}>
                            {tool.category}
                          </span>
                        </div>
                        <p className="text-gray-600 dark:text-gray-400 text-sm mb-3">
                          {tool.description}
                        </p>

                        {/* Performance Metrics */}
                        {tool.performance && (
                          <div className="flex items-center gap-6 text-sm">
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500 dark:text-gray-400">Response Time:</span>
                              <span className="font-medium text-gray-900 dark:text-gray-100">
                                {tool.performance.avgResponseTime}ms
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500 dark:text-gray-400">Success Rate:</span>
                              <span className="font-medium text-green-600 dark:text-green-400">
                                {tool.performance.successRate}%
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500 dark:text-gray-400">Usage:</span>
                              <span className="font-medium text-gray-900 dark:text-gray-100">
                                {tool.performance.usageCount.toLocaleString()}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Toggle and Expand */}
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => toggleExpanded(tool.id)}
                        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                        ) : (
                          <ChevronDown className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                        )}
                      </button>

                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={tool.enabled}
                          onChange={() => toggleTool(tool.id)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Parameters */}
                      <div>
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                          Parameters
                        </h4>
                        {tool.parameters && tool.parameters.length > 0 ? (
                          <div className="space-y-2">
                            {tool.parameters.map((param, idx) => (
                              <div
                                key={idx}
                                className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700"
                              >
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-mono text-sm text-blue-600 dark:text-blue-400">
                                    {param.name}
                                  </span>
                                  <span className="text-xs text-gray-500 dark:text-gray-400">
                                    {param.type}
                                  </span>
                                  {param.required && (
                                    <span className="text-xs text-red-600 dark:text-red-400">
                                      required
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-gray-600 dark:text-gray-400">
                                  {param.description}
                                </p>
                                {param.default !== undefined && (
                                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                                    Default: {JSON.stringify(param.default)}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            No parameters configured
                          </p>
                        )}
                      </div>

                      {/* Configuration */}
                      <div>
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                          Configuration
                        </h4>
                        <div className="space-y-2">
                          <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                              API Endpoint
                            </div>
                            <div className="font-mono text-sm text-gray-900 dark:text-gray-100">
                              {tool.apiEndpoint || 'Not configured'}
                            </div>
                          </div>

                          <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                              Tool ID
                            </div>
                            <div className="font-mono text-sm text-gray-900 dark:text-gray-100">
                              {tool.id}
                            </div>
                          </div>

                          <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                              Status
                            </div>
                            <div className="flex items-center gap-2">
                              {tool.enabled ? (
                                <>
                                  <CheckCircle className="h-4 w-4 text-green-600" />
                                  <span className="text-sm text-green-600 dark:text-green-400 font-medium">
                                    Enabled
                                  </span>
                                </>
                              ) : (
                                <>
                                  <XCircle className="h-4 w-4 text-red-600" />
                                  <span className="text-sm text-red-600 dark:text-red-400 font-medium">
                                    Disabled
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {filteredTools.length === 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
            <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">
              No tools found in this category
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
