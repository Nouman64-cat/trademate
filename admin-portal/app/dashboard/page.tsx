'use client';

/**
 * Dashboard Home Page
 *
 * Overview of key metrics and statistics with real-time data from API
 */

import * as React from 'react';
import { DashboardLayout } from '../components/dashboard-layout';
import { Users, MessageSquare, TrendingUp, Activity, Loader2 } from 'lucide-react';
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

export default function DashboardPage() {
  const [stats, setStats] = React.useState<DashboardStats | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.get<DashboardStats>('/v1/admin/stats');
      setStats(data);
    } catch (err: any) {
      console.error('Failed to fetch dashboard stats:', err);
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout breadcrumbs={[{ title: 'Dashboard' }]}>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout breadcrumbs={[{ title: 'Dashboard' }]}>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">Error: {error}</p>
          <button
            onClick={fetchStats}
            className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
          >
            Try again
          </button>
        </div>
      </DashboardLayout>
    );
  }

  if (!stats) {
    return null;
  }

  const statCards = [
    {
      title: 'Total Users',
      value: stats.total_users.toLocaleString(),
      subtext: `${stats.verified_users} verified`,
      change: stats.users_last_24h > 0 ? `+${stats.users_last_24h} today` : 'No new users today',
      trend: stats.users_last_24h > 0 ? 'up' : 'neutral',
      icon: Users,
      color: 'blue',
    },
    {
      title: 'Active Conversations',
      value: stats.total_conversations.toLocaleString(),
      subtext: `${stats.conversations_last_24h} in last 24h`,
      change: stats.conversations_last_24h > 0 ? `+${stats.conversations_last_24h}` : 'None recent',
      trend: stats.conversations_last_24h > 0 ? 'up' : 'neutral',
      icon: MessageSquare,
      color: 'green',
    },
    {
      title: 'Total Messages',
      value: stats.total_messages.toLocaleString(),
      subtext: `${stats.messages_last_24h} in last 24h`,
      change: stats.messages_last_24h > 0 ? `+${stats.messages_last_24h}` : 'None recent',
      trend: stats.messages_last_24h > 0 ? 'up' : 'neutral',
      icon: TrendingUp,
      color: 'purple',
    },
    {
      title: 'Avg Response Time',
      value: `${(stats.avg_response_time_ms / 1000).toFixed(2)}s`,
      subtext: 'Response latency',
      change: 'Performance',
      trend: 'neutral',
      icon: Activity,
      color: 'orange',
    },
  ];

  return (
    <DashboardLayout breadcrumbs={[{ title: 'Dashboard' }]}>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Dashboard
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Welcome back! Here's what's happening with TradeMate today.
            </p>
          </div>
          <button
            onClick={fetchStats}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Activity className="h-4 w-4" />
            Refresh
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statCards.map((stat) => {
            const Icon = stat.icon;
            return (
              <div
                key={stat.title}
                className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      {stat.title}
                    </p>
                    <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-gray-100">
                      {stat.value}
                    </p>
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                      {stat.subtext}
                    </p>
                    <p
                      className={`mt-2 text-sm ${
                        stat.trend === 'up'
                          ? 'text-green-600 dark:text-green-400'
                          : stat.trend === 'down'
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-gray-600 dark:text-gray-400'
                      }`}
                    >
                      {stat.change}
                    </p>
                  </div>
                  <div
                    className={`p-3 rounded-lg ${
                      stat.color === 'blue'
                        ? 'bg-blue-100 dark:bg-blue-900/20'
                        : stat.color === 'green'
                        ? 'bg-green-100 dark:bg-green-900/20'
                        : stat.color === 'purple'
                        ? 'bg-purple-100 dark:bg-purple-900/20'
                        : 'bg-orange-100 dark:bg-orange-900/20'
                    }`}
                  >
                    <Icon
                      className={`h-6 w-6 ${
                        stat.color === 'blue'
                          ? 'text-blue-600'
                          : stat.color === 'green'
                          ? 'text-green-600'
                          : stat.color === 'purple'
                          ? 'text-purple-600'
                          : 'text-orange-600'
                      }`}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* System Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              System Overview
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Active Users</span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {stats.active_users.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Verified Users</span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {stats.verified_users.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Verification Rate
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {((stats.verified_users / stats.total_users) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Messages per Conversation
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {stats.total_conversations > 0
                    ? (stats.total_messages / stats.total_conversations).toFixed(1)
                    : '0'}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Quick Actions
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <a
                href="/users"
                className="p-4 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-colors"
              >
                <Users className="h-6 w-6 text-gray-600 dark:text-gray-400 mb-2" />
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Manage Users
                </p>
              </a>
              <a
                href="/chatbot/config"
                className="p-4 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-colors"
              >
                <MessageSquare className="h-6 w-6 text-gray-600 dark:text-gray-400 mb-2" />
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Chatbot Config
                </p>
              </a>
              <a
                href="/analytics"
                className="p-4 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-colors"
              >
                <TrendingUp className="h-6 w-6 text-gray-600 dark:text-gray-400 mb-2" />
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  View Analytics
                </p>
              </a>
              <a
                href="/settings"
                className="p-4 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-colors"
              >
                <Activity className="h-6 w-6 text-gray-600 dark:text-gray-400 mb-2" />
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Settings
                </p>
              </a>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
