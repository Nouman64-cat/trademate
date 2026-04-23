'use client';

/**
 * Analytics Page
 *
 * System analytics and insights dashboard
 */

import * as React from 'react';
import { DashboardLayout } from '../components/dashboard-layout';
import { BarChart3, TrendingUp, Users, MessageSquare, Clock, Globe } from 'lucide-react';

export default function AnalyticsPage() {
  return (
    <DashboardLayout
      breadcrumbs={[{ title: 'Dashboard', href: '/dashboard' }, { title: 'Analytics' }]}
    >
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Analytics</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Comprehensive insights and performance metrics
          </p>
        </div>

        {/* Coming Soon */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
          <BarChart3 className="h-16 w-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Analytics Dashboard Coming Soon
          </h3>
          <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
            Advanced analytics, visualizations, and reporting features are currently under
            development.
          </p>
        </div>

        {/* Feature Preview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              icon: Users,
              title: 'User Analytics',
              description: 'User engagement, retention, and behavior patterns',
            },
            {
              icon: MessageSquare,
              title: 'Conversation Analytics',
              description: 'Message volume, topics, and conversation insights',
            },
            {
              icon: Clock,
              title: 'Performance Metrics',
              description: 'Response times, system health, and uptime tracking',
            },
            {
              icon: TrendingUp,
              title: 'Usage Trends',
              description: 'Historical trends and growth analytics',
            },
            {
              icon: Globe,
              title: 'Geographic Insights',
              description: 'Regional usage patterns and trade activity',
            },
            {
              icon: BarChart3,
              title: 'Custom Reports',
              description: 'Build and export custom analytical reports',
            },
          ].map((feature, index) => (
            <div
              key={index}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700"
            >
              <feature.icon className="h-8 w-8 text-blue-600 mb-3" />
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
