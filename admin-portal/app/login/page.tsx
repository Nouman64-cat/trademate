'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import {
  Database,
  Eye,
  EyeOff,
  LayoutDashboard,
  Loader2,
  Lock,
  Mail,
  ShieldCheck,
} from 'lucide-react';
import { useAuth } from '../contexts/auth-context';
import { ThemeToggle } from '../components/theme-toggle';
import { AuthSplitLayout } from '../components/auth-split-layout';
import type { AdminAuthFeature, AdminAuthStat } from '../components/auth-split-layout';
import { cn } from '../utils/cn';

// ── Brand panel content ───────────────────────────────────────────────────────

const FEATURES: AdminAuthFeature[] = [
  {
    Icon: ShieldCheck,
    title: 'Platform Security & Access Control',
    desc: 'Manage admin roles, audit API access, and enforce system policies across every service.',
  },
  {
    Icon: LayoutDashboard,
    title: 'Live Operational Oversight',
    desc: 'Monitor trade queries, freight evaluations, and AI response quality in real time.',
  },
  {
    Icon: Database,
    title: 'Data Pipeline Management',
    desc: 'Orchestrate HS datasets, document ingestion, and knowledge graph updates end to end.',
  },
];

const STATS: AdminAuthStat[] = [
  { value: '100%', label: 'Audit Trail' },
  { value: 'Live', label: 'Monitoring' },
  { value: 'Admin', label: 'Access Only' },
];

// ── Admin login form ──────────────────────────────────────────────────────────

function AdminLoginForm() {
  const [email, setEmail]               = React.useState('');
  const [password, setPassword]         = React.useState('');
  const [showPassword, setShowPassword] = React.useState(false);
  const [error, setError]               = React.useState('');
  const [isLoading, setIsLoading]       = React.useState(false);

  const { login, user } = useAuth();
  const router = useRouter();

  // Redirect if already logged in
  React.useEffect(() => {
    if (user) {
      router.push('/dashboard');
    }
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await login(email, password);
      router.push('/dashboard');
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : 'Login failed. Please check your credentials.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2 lg:invisible">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-700">
            <ShieldCheck size={14} className="text-white" />
          </div>
          <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            TradeMate Admin
          </span>
        </div>
        <ThemeToggle />
      </div>

      {/* Centered form */}
      <div className="flex flex-1 items-center justify-center px-6 py-8">
        <div className="w-full max-w-sm">
          <div className="mb-7">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-50">
              Admin Access
            </h2>
            <p className="mt-1.5 text-sm text-gray-500 dark:text-gray-400">
              Sign in to TradeMate Admin Portal
            </p>
          </div>

          {error && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3.5 dark:border-red-800 dark:bg-red-950/30">
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            {/* Email */}
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="admin-email"
                className="text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  id="admin-email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@trademate.com"
                  className="h-10 w-full rounded-lg border border-gray-300 bg-white pl-10 pr-4 text-sm text-gray-900 transition-colors placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 dark:placeholder:text-gray-500 dark:focus:border-blue-500"
                />
              </div>
            </div>

            {/* Password */}
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="admin-password"
                className="text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  id="admin-password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="h-10 w-full rounded-lg border border-gray-300 bg-white pl-10 pr-10 text-sm text-gray-900 transition-colors placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 dark:placeholder:text-gray-500 dark:focus:border-blue-500"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 transition-colors hover:text-gray-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/50 dark:hover:text-gray-300"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                'flex w-full items-center justify-center gap-2',
                'h-10 rounded-lg text-sm font-semibold transition-all',
                'bg-blue-600 text-white hover:bg-blue-700',
                'focus:outline-none focus:ring-2 focus:ring-blue-500/60 focus:ring-offset-2',
                'disabled:cursor-not-allowed disabled:opacity-60'
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 size={15} className="animate-spin" />
                  Signing in…
                </>
              ) : (
                <>
                  <Lock size={15} />
                  Sign In
                </>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-gray-500 dark:text-gray-400">
            Admin access only. Contact your system administrator if you need access.
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 text-center text-xs text-gray-400 dark:text-gray-600">
        © {new Date().getFullYear()} TradeMate. All rights reserved.
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function LoginPage() {
  return (
    <AuthSplitLayout
      badge="Secure Admin Access"
      headline={{ top: 'Command the', bottom: 'Trade Platform.' }}
      tagline="Full visibility into every user session, AI interaction, data pipeline, and system configuration — all in one secure portal."
      features={FEATURES}
      stats={STATS}
    >
      <AdminLoginForm />
    </AuthSplitLayout>
  );
}
