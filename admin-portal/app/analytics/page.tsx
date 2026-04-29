'use client';

import * as React from 'react';
import { DashboardLayout } from '../components/dashboard-layout';
import { Users, MessageSquare, Clock, TrendingUp, AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '../utils/cn';
import api from '../services/api';

interface DashboardStats {
  total_users: number;
  verified_users: number;
  active_users: number;
  total_conversations: number;
  total_messages: number;
  avg_response_time_ms: number;
  users_last_24h: number;
  conversations_last_24h: number;
  messages_last_24h: number;
}

interface DailyDataPoint {
  date: string;
  new_users: number;
  new_conversations: number;
  new_messages: number;
}

interface DailyAnalytics {
  daily: DailyDataPoint[];
  avg_response_time_ms: number;
}

export default function AnalyticsPage() {
  const [stats, setStats] = React.useState<DashboardStats | null>(null);
  const [daily, setDaily] = React.useState<DailyAnalytics | null>(null);
  const [days, setDays] = React.useState(30);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetchAll();
  }, [days]);

  const fetchAll = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, dailyData] = await Promise.all([
        api.get<DashboardStats>('/v1/admin/stats'),
        api.get<DailyAnalytics>(`/v1/admin/analytics/daily?days=${days}`),
      ]);
      setStats(statsData);
      setDaily(dailyData);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const maxMessages = daily ? Math.max(...daily.daily.map((d) => d.new_messages), 1) : 1;
  const maxConvs    = daily ? Math.max(...daily.daily.map((d) => d.new_conversations), 1) : 1;
  const maxUsers    = daily ? Math.max(...daily.daily.map((d) => d.new_users), 1) : 1;

  const avgMs = daily?.avg_response_time_ms ?? stats?.avg_response_time_ms ?? 0;

  if (loading) {
    return (
      <DashboardLayout
        breadcrumbs={[{ title: 'Dashboard', href: '/dashboard' }, { title: 'Analytics' }]}
      >
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      breadcrumbs={[{ title: 'Dashboard', href: '/dashboard' }, { title: 'Analytics' }]}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Analytics</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              System usage metrics and activity trends
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
              onClick={fetchAll}
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
            <button onClick={fetchAll} className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline">
              Try again
            </button>
          </div>
        )}

        {stats && (
          <>
            {/* Last 24 Hours */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Last 24 Hours</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                  { label: 'New Users', value: stats.users_last_24h, icon: Users, color: 'blue' },
                  { label: 'New Conversations', value: stats.conversations_last_24h, icon: TrendingUp, color: 'purple' },
                  { label: 'New Messages', value: stats.messages_last_24h, icon: MessageSquare, color: 'green' },
                ].map(({ label, value, icon: Icon, color }) => (
                  <div
                    key={label}
                    className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
                        <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                          {value.toLocaleString()}
                        </p>
                      </div>
                      <div className={cn(
                        'p-3 rounded-lg',
                        color === 'blue' && 'bg-blue-100 dark:bg-blue-900/30',
                        color === 'purple' && 'bg-purple-100 dark:bg-purple-900/30',
                        color === 'green' && 'bg-green-100 dark:bg-green-900/30',
                      )}>
                        <Icon className={cn(
                          'h-6 w-6',
                          color === 'blue' && 'text-blue-600 dark:text-blue-400',
                          color === 'purple' && 'text-purple-600 dark:text-purple-400',
                          color === 'green' && 'text-green-600 dark:text-green-400',
                        )} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* All-Time Totals */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">All-Time Totals</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Users</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                    {stats.total_users.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    {stats.verified_users.toLocaleString()} verified · {stats.active_users.toLocaleString()} active
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Conversations</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                    {stats.total_conversations.toLocaleString()}
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Messages</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                    {stats.total_messages.toLocaleString()}
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Avg Response Time</p>
                      <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                        {avgMs > 0 ? avgMs.toFixed(0) : '—'}
                        {avgMs > 0 && (
                          <span className="text-lg font-normal text-gray-500 dark:text-gray-400 ml-1">ms</span>
                        )}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {avgMs > 0 ? 'Measured from message pairs' : 'No data yet'}
                      </p>
                    </div>
                    <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                      <Clock className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                    </div>
                  </div>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Verification Rate</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                    {stats.total_users > 0
                      ? ((stats.verified_users / stats.total_users) * 100).toFixed(1)
                      : '0.0'}
                    <span className="text-lg font-normal text-gray-500 dark:text-gray-400 ml-1">%</span>
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    {stats.verified_users} of {stats.total_users} users verified
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Msgs / Conversation</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                    {stats.total_conversations > 0
                      ? (stats.total_messages / stats.total_conversations).toFixed(1)
                      : '0.0'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Average messages per session</p>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Daily Activity Trends */}
        {daily && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Activity Trends — Last {days} Days
            </h2>
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">
                        Date
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        New Users
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Conversations
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Messages
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {[...daily.daily].reverse().map((row) => (
                      <tr
                        key={row.date}
                        className="hover:bg-gray-50 dark:hover:bg-gray-900/40 transition-colors"
                      >
                        <td className="px-4 py-2.5 font-mono text-xs text-gray-600 dark:text-gray-400 whitespace-nowrap">
                          {row.date}
                        </td>
                        <td className="px-4 py-2.5">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-1.5 w-24">
                              <div
                                className="bg-blue-500 h-1.5 rounded-full"
                                style={{ width: `${(row.new_users / maxUsers) * 100}%` }}
                              />
                            </div>
                            <span className="text-xs font-medium text-gray-900 dark:text-gray-100 w-6 text-right">
                              {row.new_users}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-2.5">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-1.5 w-24">
                              <div
                                className="bg-purple-500 h-1.5 rounded-full"
                                style={{ width: `${(row.new_conversations / maxConvs) * 100}%` }}
                              />
                            </div>
                            <span className="text-xs font-medium text-gray-900 dark:text-gray-100 w-6 text-right">
                              {row.new_conversations}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-2.5">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-1.5 w-24">
                              <div
                                className="bg-green-500 h-1.5 rounded-full"
                                style={{ width: `${(row.new_messages / maxMessages) * 100}%` }}
                              />
                            </div>
                            <span className="text-xs font-medium text-gray-900 dark:text-gray-100 w-8 text-right">
                              {row.new_messages}
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
                  <span className="w-3 h-1.5 bg-blue-500 rounded-full inline-block" /> Users
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-1.5 bg-purple-500 rounded-full inline-block" /> Conversations
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-1.5 bg-green-500 rounded-full inline-block" /> Messages
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
