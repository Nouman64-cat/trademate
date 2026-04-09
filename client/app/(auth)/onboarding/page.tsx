"use client";

import { useState } from "react";
import { Loader2, Briefcase, Globe, Building2, Languages, UserCog } from "lucide-react";
import { useOnboarding } from "@/hooks/useAuth";
import { SelectField, InputField } from "@/components/ui/FormField";
import { AlertMessage } from "@/components/ui/AlertMessage";
import type { OnboardingRequest, TradeRole } from "@/types/auth";
import { cn } from "@/lib/cn";

const TRADE_ROLES: { value: TradeRole; label: string }[] = [
  { value: "importer", label: "Importer" },
  { value: "exporter", label: "Exporter" },
  { value: "both", label: "Both (Importer & Exporter)" },
];

const USER_TYPES = [
  { value: "individual", label: "Individual" },
  { value: "company", label: "Company" },
  { value: "institution", label: "Institution" },
];

const TARGET_REGIONS = [
  { value: "asia_pacific", label: "Asia-Pacific" },
  { value: "middle_east", label: "Middle East" },
  { value: "europe", label: "Europe" },
  { value: "north_america", label: "North America" },
  { value: "africa", label: "Africa" },
  { value: "latin_america", label: "Latin America" },
  { value: "global", label: "Global" },
];

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "ar", label: "Arabic" },
  { value: "zh", label: "Chinese" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
];

const INITIAL: OnboardingRequest = {
  trade_role: "importer",
  user_type: "",
  company_name: "",
  target_region: "",
  language_preference: "",
};

export default function OnboardingPage() {
  const { submitOnboarding, isLoading, error } = useOnboarding();
  const [form, setForm] = useState<OnboardingRequest>(INITIAL);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof OnboardingRequest, string>>>({});

  const set =
    (key: keyof OnboardingRequest) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const validate = (): boolean => {
    const errors: Partial<Record<keyof OnboardingRequest, string>> = {};
    if (!form.trade_role) errors.trade_role = "Select your trade role.";
    if (!form.user_type) errors.user_type = "Select your user type.";
    if (!form.company_name.trim()) errors.company_name = "Company name is required.";
    if (!form.target_region) errors.target_region = "Select a target region.";
    if (!form.language_preference) errors.language_preference = "Select a language.";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    await submitOnboarding(form);
  };

  return (
    <div className="w-full max-w-lg">
      {/* Card */}
      <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm p-8">
        {/* Heading */}
        <div className="mb-7 text-center">
          <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
            Set up your profile
          </h1>
          <p className="mt-1.5 text-sm text-zinc-500 dark:text-zinc-400 max-w-sm mx-auto">
            Help us personalise TradeMate to your trading context. This takes
            less than a minute.
          </p>
        </div>

        {error && <AlertMessage type="error" message={error} className="mb-5" />}

        <form onSubmit={handleSubmit} noValidate className="space-y-5">
          {/* Row 1 */}
          <div className="grid grid-cols-2 gap-4">
            <SelectField
              label="Trade Role"
              options={TRADE_ROLES}
              value={form.trade_role}
              onChange={set("trade_role")}
              error={fieldErrors.trade_role}
              placeholder="Select role"
            />
            <SelectField
              label="User Type"
              options={USER_TYPES}
              value={form.user_type}
              onChange={set("user_type")}
              error={fieldErrors.user_type}
              placeholder="Select type"
            />
          </div>

          {/* Company */}
          <InputField
            label="Company / Organisation Name"
            type="text"
            placeholder="Acme Trading Co."
            value={form.company_name}
            onChange={set("company_name")}
            error={fieldErrors.company_name}
          />

          {/* Row 2 */}
          <div className="grid grid-cols-2 gap-4">
            <SelectField
              label="Target Region"
              options={TARGET_REGIONS}
              value={form.target_region}
              onChange={set("target_region")}
              error={fieldErrors.target_region}
              placeholder="Select region"
            />
            <SelectField
              label="Preferred Language"
              options={LANGUAGES}
              value={form.language_preference}
              onChange={set("language_preference")}
              error={fieldErrors.language_preference}
              placeholder="Select language"
            />
          </div>

          {/* Summary chips — visual only, shows what the user picked */}
          {(form.trade_role || form.target_region) && (
            <ProfileSummary form={form} />
          )}

          <button
            type="submit"
            disabled={isLoading}
            className={cn(
              "w-full h-10 rounded-lg text-sm font-semibold transition-all mt-1",
              "bg-gradient-to-r from-violet-600 to-indigo-600",
              "text-white hover:from-violet-500 hover:to-indigo-500",
              "focus:outline-none focus:ring-2 focus:ring-violet-400/60 focus:ring-offset-2",
              "disabled:opacity-60 disabled:cursor-not-allowed",
              "flex items-center justify-center gap-2"
            )}
          >
            {isLoading && <Loader2 size={15} className="animate-spin" />}
            {isLoading ? "Saving…" : "Get started"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ── Profile summary chips ────────────────────────────────────────────────────

function ProfileSummary({ form }: { form: OnboardingRequest }) {
  const chips = [
    { icon: <Briefcase size={11} />, value: form.trade_role },
    { icon: <UserCog size={11} />, value: form.user_type },
    { icon: <Building2 size={11} />, value: form.company_name },
    { icon: <Globe size={11} />, value: form.target_region?.replace("_", " ") },
    { icon: <Languages size={11} />, value: form.language_preference },
  ].filter((c) => c.value);

  if (!chips.length) return null;

  return (
    <div className="flex flex-wrap gap-1.5 pt-1">
      {chips.map((chip, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-violet-50 dark:bg-violet-950/40 text-violet-700 dark:text-violet-300 border border-violet-200 dark:border-violet-800/50 capitalize"
        >
          {chip.icon}
          {chip.value}
        </span>
      ))}
    </div>
  );
}
