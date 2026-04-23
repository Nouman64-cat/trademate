'use client';

/**
 * Settings Page
 *
 * System settings and configuration
 */

import * as React from 'react';
import { DashboardLayout } from '../components/dashboard-layout';
import { Settings, Bell, Shield, Database, Mail, Key, Palette, Globe } from 'lucide-react';

export default function SettingsPage() {
  return (
    <DashboardLayout
      breadcrumbs={[{ title: 'Dashboard', href: '/dashboard' }, { title: 'Settings' }]}
    >
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage system configuration and preferences
          </p>
        </div>

        {/* Coming Soon */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
          <Settings className="h-16 w-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Settings Panel Coming Soon
          </h3>
          <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
            Advanced system settings and configuration options are currently under development.
          </p>
        </div>

        {/* Settings Categories Preview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              icon: Bell,
              title: 'Notifications',
              description: 'Configure email and system notifications',
            },
            {
              icon: Shield,
              title: 'Security',
              description: 'Password policies, 2FA, and access control',
            },
            {
              icon: Database,
              title: 'Data & Backup',
              description: 'Database settings and automated backups',
            },
            {
              icon: Mail,
              title: 'Email Configuration',
              description: 'SMTP settings and email templates',
            },
            {
              icon: Key,
              title: 'API Keys',
              description: 'Manage third-party API integrations',
            },
            {
              icon: Palette,
              title: 'Appearance',
              description: 'Branding, themes, and customization',
            },
            {
              icon: Globe,
              title: 'Localization',
              description: 'Language, timezone, and regional settings',
            },
            {
              icon: Settings,
              title: 'Advanced',
              description: 'System maintenance and developer options',
            },
          ].map((setting, index) => (
            <div
              key={index}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700"
            >
              <setting.icon className="h-8 w-8 text-blue-600 mb-3" />
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                {setting.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{setting.description}</p>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
