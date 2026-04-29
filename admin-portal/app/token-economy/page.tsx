'use client';

import * as React from 'react';
import { DashboardLayout } from '../components/dashboard-layout';
import { Zap, DollarSign, MessageSquare, TrendingUp, AlertCircle, RefreshCw, Bot } from 'lucide-react';
import { cn } from '../utils/cn';
import api from '../services/api';

interface ModelTokenStats {
  model_name: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  message_count: number;
}

interface UserTokenStats {
  user_id: number;
  email: string;
  full_name: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  message_count: number;
}

interface DailyTokenStats {
  date: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
}

interface TokenEconomyData {
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
  tracked_messages: number;
  by_model: ModelTokenStats[];
  by_user: UserTokenStats[];
  daily: DailyTokenStats[];
}

function fmt(n: number) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return n.toLocaleString();
}

function fmtCost(usd: number) {
  if (usd === 0) return '$0.0000';
  if (usd < 0.01) return `$${usd.toFixed(6)}`;
  if (usd < 1) return `$${usd.toFixed(4)}`;
  return `$${usd.toFixed(2)}`;
}

function Bar({ pct, color }: { pct: number; color: string }) {
  return (
    <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-1.5 min-w-[60px]">
      <div
        className={cn('h-1.5 rounded-full transition-all', color)}
        style={{ width: `${Math.min(100, pct)}%` }}
      />
    </div>
  );
}

export default function TokenEconomyPage() {
  const [data, setData] = React.useState<TokenEconomyData | null>(null);
  const [days, setDays] = React.useState(30);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetchData();
  }, [days]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.get<TokenEconomyData>(`/v1/admin/token-economy?days=${days}`);
      setData(result);
    } catch (err: any) {
      setError(err.message || 'Failed to load token economy data');
    } finally {
      setLoading(false);
    }
  };

  const maxModelTokens = data ? Math.max(...data.by_model.map((m) => m.total_tokens), 1) : 1;
  const maxModelCost   = data ? Math.max(...data.by_model.map((m) => m.cost_usd), 0.000001) : 0.000001;
  const maxUserTokens  = data ? Math.max(...data.by_user.map((u) => u.total_tokens), 1) : 1;
  const maxUserCost    = data ? Math.max(...data.by_user.map((u) => u.cost_usd), 0.000001) : 0.000001;
  const maxDailyTokens = data ? Math.max(...data.daily.map((d) => d.total_tokens), 1) : 1;
  const maxDailyCost   = data ? Math.max(...data.daily.map((d) => d.cost_usd), 0.000001) : 0.000001;

  const avgCostPerMsg = data && data.tracked_messages > 0
    ? data.total_cost_usd / data.tracked_messages
    : 0;
  const avgTokensPerMsg = data && data.tracked_messages > 0
    ? data.total_tokens / data.tracked_messages
    : 0;

  if (loading) {
    return (
      <DashboardLayout
        breadcrumbs={[{ title: 'Dashboard', href: '/dashboard' }, { title: 'Token Economy' }]}
      >
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      breadcrumbs={[{ title: 'Dashboard', href: '/dashboard' }, { title: 'Token Economy' }]}
    >
      <div className="space-y-8">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Token Economy</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              LLM token usage, cost breakdown, and spending trends
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={7}>Last 7 days</option>
              <option value={14}>Last 14 days</option>
              <option value={30}>Last 30 days</option>
              <option value={60}>Last 60 days</option>
              <option value={90}>Last 90 days</option>
            </select>
            <button
              onClick={fetchData}
              className="inline-flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
              <p className="text-red-800 dark:text-red-200">{error}</p>
            </div>
            <button onClick={fetchData} className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline">
              Try again
            </button>
          </div>
        )}

        {data && (
          <>
            {/* ── Stat cards ─────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                {
                  label: 'Total Tokens Used',
                  value: fmt(data.total_tokens),
                  sub: `${fmt(data.total_prompt_tokens)} prompt · ${fmt(data.total_completion_tokens)} completion`,
                  icon: Zap,
                  bg: 'bg-blue-100 dark:bg-blue-900/30',
                  iconCls: 'text-blue-600 dark:text-blue-400',
                },
                {
                  label: 'Total Cost',
                  value: fmtCost(data.total_cost_usd),
                  sub: `${data.tracked_messages.toLocaleString()} tracked messages`,
                  icon: DollarSign,
                  bg: 'bg-green-100 dark:bg-green-900/30',
                  iconCls: 'text-green-600 dark:text-green-400',
                },
                {
                  label: 'Avg Tokens / Message',
                  value: fmt(Math.round(avgTokensPerMsg)),
                  sub: 'per assistant reply',
                  icon: MessageSquare,
                  bg: 'bg-purple-100 dark:bg-purple-900/30',
                  iconCls: 'text-purple-600 dark:text-purple-400',
                },
                {
                  label: 'Avg Cost / Message',
                  value: fmtCost(avgCostPerMsg),
                  sub: 'per assistant reply',
                  icon: TrendingUp,
                  bg: 'bg-orange-100 dark:bg-orange-900/30',
                  iconCls: 'text-orange-600 dark:text-orange-400',
                },
              ].map(({ label, value, sub, icon: Icon, bg, iconCls }) => (
                <div
                  key={label}
                  className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
                      <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2 truncate">
                        {value}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 truncate">{sub}</p>
                    </div>
                    <div className={cn('p-3 rounded-lg ml-3 shrink-0', bg)}>
                      <Icon className={cn('h-6 w-6', iconCls)} />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* ── Prompt vs Completion split ────────────────────────────── */}
            {data.total_tokens > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
                <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Token Split — Prompt vs Completion
                </h2>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <span className="w-28 text-sm text-gray-600 dark:text-gray-400 shrink-0">Prompt</span>
                    <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-4">
                      <div
                        className="bg-blue-500 h-4 rounded-full flex items-center justify-end pr-2 transition-all"
                        style={{ width: `${(data.total_prompt_tokens / data.total_tokens) * 100}%` }}
                      >
                        <span className="text-[10px] text-white font-medium">
                          {((data.total_prompt_tokens / data.total_tokens) * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <span className="w-20 text-sm font-medium text-gray-900 dark:text-gray-100 text-right">
                      {fmt(data.total_prompt_tokens)}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="w-28 text-sm text-gray-600 dark:text-gray-400 shrink-0">Completion</span>
                    <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-4">
                      <div
                        className="bg-purple-500 h-4 rounded-full flex items-center justify-end pr-2 transition-all"
                        style={{ width: `${(data.total_completion_tokens / data.total_tokens) * 100}%` }}
                      >
                        <span className="text-[10px] text-white font-medium">
                          {((data.total_completion_tokens / data.total_tokens) * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <span className="w-20 text-sm font-medium text-gray-900 dark:text-gray-100 text-right">
                      {fmt(data.total_completion_tokens)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* ── Model Breakdown ───────────────────────────────────────── */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
                <Bot className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                  Usage by Model
                </h2>
              </div>
              {data.by_model.length === 0 ? (
                <div className="px-6 py-12 text-center text-gray-500 dark:text-gray-400 text-sm">
                  No token data yet — token tracking starts with new messages.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Model</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Tokens</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Prompt</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Completion</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Cost (USD)</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Messages</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {data.by_model.map((m) => (
                        <tr key={m.model_name} className="hover:bg-gray-50 dark:hover:bg-gray-900/40 transition-colors">
                          <td className="px-6 py-3">
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">
                              {m.model_name}
                            </span>
                          </td>
                          <td className="px-6 py-3">
                            <div className="flex items-center gap-2">
                              <Bar pct={(m.total_tokens / maxModelTokens) * 100} color="bg-blue-500" />
                              <span className="text-xs font-medium text-gray-900 dark:text-gray-100 w-14 text-right">
                                {fmt(m.total_tokens)}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-3 text-xs text-gray-600 dark:text-gray-400">{fmt(m.prompt_tokens)}</td>
                          <td className="px-6 py-3 text-xs text-gray-600 dark:text-gray-400">{fmt(m.completion_tokens)}</td>
                          <td className="px-6 py-3">
                            <div className="flex items-center gap-2">
                              <Bar pct={(m.cost_usd / maxModelCost) * 100} color="bg-green-500" />
                              <span className="text-xs font-medium text-gray-900 dark:text-gray-100 w-20 text-right">
                                {fmtCost(m.cost_usd)}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-3 text-right text-xs font-medium text-gray-900 dark:text-gray-100">
                            {m.message_count.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* ── Per-User Table ────────────────────────────────────────── */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                  Usage by User
                </h2>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Top 100 users by total cost, all-time
                </p>
              </div>
              {data.by_user.length === 0 ? (
                <div className="px-6 py-12 text-center text-gray-500 dark:text-gray-400 text-sm">
                  No tracked user data yet.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">#</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">User</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Tokens</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Prompt</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Completion</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Cost (USD)</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Messages</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {data.by_user.map((u, i) => (
                        <tr key={u.user_id} className="hover:bg-gray-50 dark:hover:bg-gray-900/40 transition-colors">
                          <td className="px-6 py-3 text-xs text-gray-400 dark:text-gray-500 font-mono">
                            {i + 1}
                          </td>
                          <td className="px-6 py-3">
                            <div>
                              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate max-w-[180px]">
                                {u.full_name}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[180px]">
                                {u.email}
                              </p>
                            </div>
                          </td>
                          <td className="px-6 py-3">
                            <div className="flex items-center gap-2">
                              <Bar pct={(u.total_tokens / maxUserTokens) * 100} color="bg-blue-400" />
                              <span className="text-xs font-medium text-gray-900 dark:text-gray-100 w-14 text-right">
                                {fmt(u.total_tokens)}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-3 text-xs text-gray-500 dark:text-gray-400">{fmt(u.prompt_tokens)}</td>
                          <td className="px-6 py-3 text-xs text-gray-500 dark:text-gray-400">{fmt(u.completion_tokens)}</td>
                          <td className="px-6 py-3">
                            <div className="flex items-center gap-2">
                              <Bar pct={(u.cost_usd / maxUserCost) * 100} color="bg-emerald-500" />
                              <span className="text-xs font-medium text-gray-900 dark:text-gray-100 w-20 text-right">
                                {fmtCost(u.cost_usd)}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-3 text-right text-xs font-medium text-gray-900 dark:text-gray-100">
                            {u.message_count.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* ── Daily Token Trends ────────────────────────────────────── */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                  Daily Token Trends — Last {days} Days
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Tokens</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Prompt</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Completion</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Cost (USD)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {[...data.daily].reverse().map((row) => (
                      <tr
                        key={row.date}
                        className="hover:bg-gray-50 dark:hover:bg-gray-900/40 transition-colors"
                      >
                        <td className="px-4 py-2.5 font-mono text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                          {row.date}
                        </td>
                        <td className="px-4 py-2.5">
                          <div className="flex items-center gap-2">
                            <Bar pct={(row.total_tokens / maxDailyTokens) * 100} color="bg-blue-500" />
                            <span className="text-xs font-medium text-gray-900 dark:text-gray-100 w-14 text-right">
                              {fmt(row.total_tokens)}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-2.5 text-xs text-gray-500 dark:text-gray-400">{fmt(row.prompt_tokens)}</td>
                        <td className="px-4 py-2.5 text-xs text-gray-500 dark:text-gray-400">{fmt(row.completion_tokens)}</td>
                        <td className="px-4 py-2.5">
                          <div className="flex items-center gap-2">
                            <Bar pct={(row.cost_usd / maxDailyCost) * 100} color="bg-green-500" />
                            <span className="text-xs font-medium text-gray-900 dark:text-gray-100 w-20 text-right">
                              {fmtCost(row.cost_usd)}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-700 flex items-center gap-6 text-xs text-gray-500 dark:text-gray-400">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-1.5 bg-blue-500 rounded-full inline-block" /> Tokens
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-1.5 bg-green-500 rounded-full inline-block" /> Cost
                </span>
              </div>
            </div>

            {/* ── Pricing reference ─────────────────────────────────────── */}
            <div className="bg-gray-50 dark:bg-gray-900/40 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                Pricing Reference (per 1M tokens)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {[
                  { model: 'gpt-4o',        prompt: '$5.00',  completion: '$15.00' },
                  { model: 'gpt-4o-mini',   prompt: '$0.15',  completion: '$0.60' },
                  { model: 'gpt-4-turbo',   prompt: '$10.00', completion: '$30.00' },
                  { model: 'gpt-4',         prompt: '$30.00', completion: '$60.00' },
                  { model: 'gpt-3.5-turbo', prompt: '$0.50',  completion: '$1.50' },
                  { model: 'gpt-5.4',       prompt: '$10.00', completion: '$30.00' },
                ].map(({ model, prompt, completion }) => (
                  <div key={model} className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                    <p className="text-xs font-semibold text-gray-900 dark:text-gray-100 truncate">{model}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">In: {prompt}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Out: {completion}</p>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
                Costs are estimates based on OpenAI pricing. gpt-5.4 uses gpt-4-turbo equivalent pricing.
              </p>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
