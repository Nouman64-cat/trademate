'use client';

import * as React from 'react';
import { DashboardLayout } from '../components/dashboard-layout';
import { Settings, Shield } from 'lucide-react';
import Link from 'next/link';

export default function SettingsPage() {
  return (
    <DashboardLayout
      breadcrumbs={[{ title: 'Dashboard', href: '/dashboard' }, { title: 'Settings' }]}
    >
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage system configuration and preferences
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Link
            href="/settings/general"
            className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-md transition-all"
          >
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Settings className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-lg">
                  General Settings
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Site name, support email, maintenance mode, language, and timezone
                </p>
              </div>
            </div>
          </Link>

          <Link
            href="/settings/security"
            className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-md transition-all"
          >
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <Shield className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-lg">
                  Security Settings
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Password policies, session timeout, rate limits, and access control
                </p>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </DashboardLayout>
  );
}
