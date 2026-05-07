"use client";

import { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff, Globe, Loader2, Package, TrendingUp } from "lucide-react";
import { useRegister } from "@/hooks/useAuth";
import { InputField } from "@/components/ui/FormField";
import { AlertMessage } from "@/components/ui/AlertMessage";
import { AuthSplitLayout } from "@/components/ui/AuthSplitLayout";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { cn } from "@/lib/cn";
import type { AuthFeature, AuthStat } from "@/components/ui/AuthSplitLayout";

// ── Brand panel content ───────────────────────────────────────────────────────

const FEATURES: AuthFeature[] = [
  {
    Icon: Package,
    title: "Ready in Under a Minute",
    desc: "From signup to your first HS classification — the entire setup takes less than 60 seconds.",
  },
  {
    Icon: Globe,
    title: "Access PAK & USA Global Markets",
    desc: "Navigate tariffs, regulations, and freight options across every major international trade lane.",
  },
  {
    Icon: TrendingUp,
    title: "Scale Without the Overhead",
    desc: "Replace manual compliance workflows with AI that classifies, advises, and quotes in real time.",
  },
];

const STATS: AuthStat[] = [
  { value: "Free", label: "To Start" },
  { value: "PAK & USA", label: "Markets" },
  { value: "< 60s", label: "Setup" },
];

// ── Form state type ───────────────────────────────────────────────────────────

interface FormState {
  username: string;
  email: string;
  password: string;
  phone_number: string;
}

const INITIAL: FormState = {
  username: "",
  email: "",
  password: "",
  phone_number: "",
};

// ── Register form ─────────────────────────────────────────────────────────────

function RegisterForm() {
  const { register, isLoading, error } = useRegister();
  const [form, setForm] = useState<FormState>(INITIAL);
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Partial<FormState>>({});

  const set =
    (key: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const validate = (): boolean => {
    const errors: Partial<FormState> = {};
    if (!form.username.trim()) errors.username = "Username is required.";
    if (!form.email.trim()) errors.email = "Email is required.";
    else if (!/\S+@\S+\.\S+/.test(form.email)) errors.email = "Enter a valid email.";
    if (!form.password) errors.password = "Password is required.";
    else if (form.password.length < 8) errors.password = "Must be at least 8 characters.";
    if (!form.phone_number.trim()) errors.phone_number = "Phone number is required.";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    await register(form);
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
              Create your account
            </h2>
            <p className="mt-1.5 text-sm text-zinc-500 dark:text-zinc-400">
              Start your TradeMate journey today
            </p>
          </div>

          {error && <AlertMessage type="error" message={error} className="mb-4" />}

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <InputField
              label="Username"
              type="text"
              placeholder="johndoe"
              autoComplete="username"
              value={form.username}
              onChange={set("username")}
              error={fieldErrors.username}
            />
            <InputField
              label="Email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              value={form.email}
              onChange={set("email")}
              error={fieldErrors.email}
            />

            {/* Password with show/hide toggle */}
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="register-password"
                className="text-sm font-medium text-zinc-700 dark:text-zinc-300"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="register-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Min. 8 characters"
                  autoComplete="new-password"
                  value={form.password}
                  onChange={set("password")}
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

            <InputField
              label="Phone Number"
              type="tel"
              placeholder="+1 555 000 0000"
              autoComplete="tel"
              value={form.phone_number}
              onChange={set("phone_number")}
              error={fieldErrors.phone_number}
            />

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
              {isLoading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-zinc-500 dark:text-zinc-400">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-medium text-violet-600 hover:underline dark:text-violet-400"
            >
              Sign in
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

export default function RegisterPage() {
  return (
    <AuthSplitLayout
      badge="Join TradeMate Today"
      headline={{ top: "Your Gateway to", bottom: "Global Trade." }}
      tagline="Create your account and unlock AI-powered trade intelligence — from HS code classification to live freight rates."
      features={FEATURES}
      stats={STATS}
    >
      <RegisterForm />
    </AuthSplitLayout>
  );
}
