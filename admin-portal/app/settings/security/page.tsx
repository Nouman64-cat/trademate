'use client';

import * as React from 'react';
import { DashboardLayout } from '../../components/dashboard-layout';
import { 
  Save, 
  RefreshCw, 
  Loader2, 
  Lock, 
  ShieldCheck, 
  Key, 
  UserX,
  Smartphone,
  Timer,
  Clock
} from 'lucide-react';
import { cn } from '../../utils/cn';
import type { SecuritySettings } from '../../types';
import api from '../../services/api';

export default function SecuritySettingsPage() {
  const [settings, setSettings] = React.useState<SecuritySettings | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.get<SecuritySettings>('/v1/admin/settings/security');
      setSettings(data);
    } catch (err: any) {
      console.error('Failed to fetch security settings:', err);
      setError(err.message || 'Failed to load security settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    try {
      setSaving(true);
      setError(null);
      await api.put('/v1/admin/settings/security', settings);
      alert('Security settings saved successfully!');
    } catch (err: any) {
      console.error('Failed to save security settings:', err);
      setError(err.message || 'Failed to save security settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout
        breadcrumbs={[
          { title: 'Dashboard', href: '/dashboard' },
          { title: 'Settings', href: '/settings' },
          { title: 'Security' },
        ]}
      >
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      </DashboardLayout>
    );
  }

  if (error || !settings) {
    return (
      <DashboardLayout
        breadcrumbs={[
          { title: 'Dashboard', href: '/dashboard' },
          { title: 'Settings', href: '/settings' },
          { title: 'Security' },
        ]}
      >
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">Error: {error}</p>
          <button
            onClick={fetchSettings}
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
        { title: 'Settings', href: '/settings' },
        { title: 'Security' },
      ]}
    >
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Security Settings
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Manage platform authentication policies, password requirements, and session controls
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={fetchSettings}
              className="inline-flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
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

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Password Policy */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="flex items-center gap-2 mb-6">
              <Key className="h-5 w-5 text-blue-600" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Password Policy
              </h2>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Minimum Password Length
                </label>
                <input
                  type="number"
                  min="6"
                  max="32"
                  value={settings.min_password_length}
                  onChange={(e) => setSettings({ ...settings, min_password_length: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Require Special Characters</p>
                  <p className="text-xs text-gray-500">Must include symbols like @, #, $</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.require_special_characters}
                  onChange={(e) => setSettings({ ...settings, require_special_characters: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Require Numbers</p>
                  <p className="text-xs text-gray-500">Must include at least one digit</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.require_numbers}
                  onChange={(e) => setSettings({ ...settings, require_numbers: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>
            </div>
          </div>

          {/* Authentication & Sessions */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="flex items-center gap-2 mb-6">
              <ShieldCheck className="h-5 w-5 text-blue-600" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Auth & Sessions
              </h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-100 dark:border-blue-900/30">
                <div className="flex gap-3">
                  <Smartphone className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-300">Require 2FA</p>
                    <p className="text-xs text-blue-700/70 dark:text-blue-400/60">Enforce Two-Factor Auth for all users</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={settings.two_factor_required}
                  onChange={(e) => setSettings({ ...settings, two_factor_required: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>

              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  <Timer className="h-4 w-4" />
                  Session Timeout (Minutes)
                </label>
                <input
                  type="number"
                  min="5"
                  max="1440"
                  value={settings.session_timeout_minutes}
                  onChange={(e) => setSettings({ ...settings, session_timeout_minutes: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  JWT Access Token Expiry (Min)
                </label>
                <input
                  type="number"
                  min="1"
                  max="60"
                  value={settings.jwt_access_token_expire_minutes}
                  onChange={(e) => setSettings({ ...settings, jwt_access_token_expire_minutes: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* brute force protection */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 shadow-sm md:col-span-2">
            <div className="flex items-center gap-2 mb-6">
              <UserX className="h-5 w-5 text-red-600" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Brute Force Protection
              </h2>
            </div>
            
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Max Login Attempts Before Account Lock
                </label>
                <p className="text-sm text-gray-500 mb-4">
                  Number of failed attempts allowed before a user is temporarily blocked. 
                  Users can unlock via email verification.
                </p>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="3"
                    max="20"
                    value={settings.max_login_attempts}
                    onChange={(e) => setSettings({ ...settings, max_login_attempts: parseInt(e.target.value) })}
                    className="flex-1"
                  />
                  <span className="w-12 text-center font-bold text-gray-700 dark:text-gray-300 px-2 py-1 bg-gray-100 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
                    {settings.max_login_attempts}
                  </span>
                </div>
              </div>
              
              <div className="p-4 bg-red-50 dark:bg-red-900/10 rounded-lg border border-red-100 dark:border-red-900/30 max-w-sm">
                <div className="flex gap-3">
                  <Lock className="h-5 w-5 text-red-600 mt-0.5" />
                  <p className="text-xs text-red-800 dark:text-red-300 font-medium">
                    Warning: Setting this too low may result in accidental account locks for legitimate users with poor connectivity or forgotten passwords.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="text-[10px] text-gray-400 flex items-center gap-1">
          <Clock className="h-3 w-3" />
          <span>Security policy last synced: {new Date(settings.updated_at).toLocaleString()}</span>
        </div>
      </div>
    </DashboardLayout>
  );
}
