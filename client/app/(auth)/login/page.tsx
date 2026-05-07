"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Eye, EyeOff, Loader2, TrendingUp, Globe, ShieldCheck, Zap } from "lucide-react";
import { useLogin } from "@/hooks/useAuth";
import { InputField } from "@/components/ui/FormField";
import { AlertMessage } from "@/components/ui/AlertMessage";
import { AuthSplitLayout } from "@/components/ui/AuthSplitLayout";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { cn } from "@/lib/cn";
import type { AuthFeature, AuthStat } from "@/components/ui/AuthSplitLayout";

// ── Brand panel content ───────────────────────────────────────────────────────

const FEATURES: AuthFeature[] = [
  {
    Icon: Zap,
    title: "Instant HS Code Classification",
    desc: "AI classifies any product in milliseconds — no tariff manuals required.",
  },
  {
    Icon: Globe,
    title: "Live Global Freight Rates",
    desc: "Real-time quotes from 50+ carriers across sea, air, and road networks.",
  },
  {
    Icon: ShieldCheck,
    title: "Customs & Compliance Intelligence",
    desc: "Regulatory guidance for DRAP, FDA, and cross-border tariff advisory.",
  },
];

const STATS: AuthStat[] = [
  { value: "50+", label: "Carriers" },
  { value: "PAK & USA", label: "Countries" },
  { value: "<2s", label: "Classification" },
];

// ── Login form ────────────────────────────────────────────────────────────────

function LoginForm() {
  const searchParams = useSearchParams();
  const justRegistered = searchParams.get("registered") === "1";
  const justReset = searchParams.get("reset") === "1";

  const { login, isLoading, error } = useLogin();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const errors: Record<string, string> = {};
    if (!email.trim()) errors.email = "Email is required.";
    else if (!/\S+@\S+\.\S+/.test(email)) errors.email = "Enter a valid email.";
    if (!password) errors.password = "Password is required.";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    await login({ email, password });
  };

  return (
    <div className="flex min-h-screen flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2 lg:invisible">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600">
            <TrendingUp size={14} className="text-white" />
          </div>
          <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            TradeMate
          </span>
        </div>
        <ThemeToggle />
      </div>

      {/* Centered form */}
      <div className="flex flex-1 items-center justify-center px-6 py-8">
        <div className="w-full max-w-sm">
          <div className="mb-7">
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
              Welcome back
            </h2>
            <p className="mt-1.5 text-sm text-zinc-500 dark:text-zinc-400">
              Sign in to your TradeMate account
            </p>
          </div>

          {justRegistered && (
            <AlertMessage
              type="success"
              message="Account created! Please sign in."
              className="mb-4"
            />
          )}
          {justReset && (
            <AlertMessage
              type="success"
              message="Password updated! Please sign in with your new password."
              className="mb-4"
            />
          )}
          {error && <AlertMessage type="error" message={error} className="mb-4" />}

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <InputField
              label="Email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={fieldErrors.email}
            />

            {/* Password with show/hide toggle */}
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="password"
                className="text-sm font-medium text-zinc-700 dark:text-zinc-300"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={cn(
                    "h-10 w-full rounded-lg border px-3 pr-10 text-sm",
                    "bg-white dark:bg-zinc-800/60",
                    "text-zinc-900 dark:text-zinc-100",
                    "placeholder:text-zinc-400 dark:placeholder:text-zinc-500",
                    "transition-colors",
                    fieldErrors.password
                      ? "border-red-400 dark:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-400/40"
                      : "border-zinc-200 dark:border-zinc-700 focus:outline-none focus:ring-2 focus:ring-violet-400/50 focus:border-violet-400 dark:focus:border-violet-500"
                  )}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-zinc-400 transition-colors hover:text-zinc-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400/50 dark:hover:text-zinc-300"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {fieldErrors.password && (
                <p className="text-xs text-red-500 dark:text-red-400">
                  {fieldErrors.password}
                </p>
              )}
            </div>

            <div className="text-right">
              <Link
                href="/forgot-password"
                className="text-xs text-violet-600 hover:underline dark:text-violet-400"
              >
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                "flex w-full items-center justify-center gap-2",
                "h-10 rounded-lg text-sm font-semibold transition-all",
                "bg-gradient-to-r from-violet-600 to-indigo-600",
                "text-white hover:from-violet-500 hover:to-indigo-500",
                "focus:outline-none focus:ring-2 focus:ring-violet-400/60 focus:ring-offset-2",
                "disabled:cursor-not-allowed disabled:opacity-60"
              )}
            >
              {isLoading && <Loader2 size={15} className="animate-spin" />}
              {isLoading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-zinc-500 dark:text-zinc-400">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              className="font-medium text-violet-600 hover:underline dark:text-violet-400"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 text-center text-xs text-zinc-400 dark:text-zinc-600">
        © {new Date().getFullYear()} TradeMate. All rights reserved.
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function LoginPage() {
  return (
    <AuthSplitLayout
      badge="AI-Powered Trade Intelligence"
      headline={{ top: "Trade Smarter.", bottom: "Reach Further." }}
      tagline="One platform for HS classification, live freight rates, and cross-border compliance — built for teams that move the world's goods."
      features={FEATURES}
      stats={STATS}
    >
      <Suspense>
        <LoginForm />
      </Suspense>
    </AuthSplitLayout>
  );
}
