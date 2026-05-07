"use client";

import { TrendingUp } from "lucide-react";
import { MouseTrackGlow } from "@/components/ui/MouseTrackGlow";

export interface AuthFeature {
  Icon: React.ComponentType<{ size?: number; className?: string }>;
  title: string;
  desc: string;
}

export interface AuthStat {
  value: string;
  label: string;
}

export interface AuthSplitLayoutProps {
  badge: string;
  headline: { top: string; bottom: string };
  tagline: string;
  features: AuthFeature[];
  stats?: AuthStat[];
  children: React.ReactNode;
}

export function AuthSplitLayout({
  badge,
  headline,
  tagline,
  features,
  stats,
  children,
}: AuthSplitLayoutProps) {
  return (
    <div className="fixed inset-0 z-50 flex bg-white dark:bg-zinc-950">
      {/* ── Left: interactive brand panel — desktop only ── */}
      <div className="hidden lg:flex lg:w-[55%] xl:w-[58%]">
        <MouseTrackGlow className="flex flex-1 flex-col bg-gradient-to-br from-slate-900 via-[#1e0533] to-indigo-950">
          {/* Grid texture */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 opacity-[0.035]"
            style={{
              backgroundImage:
                "linear-gradient(rgba(255,255,255,0.7) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.7) 1px, transparent 1px)",
              backgroundSize: "52px 52px",
            }}
          />

          {/* Static corner accent glow */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full"
            style={{ background: "rgba(99,102,241,0.12)", filter: "blur(80px)" }}
          />

          {/* Logo */}
          <div className="relative z-10 flex items-center gap-2.5 p-8">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 shadow-lg shadow-violet-500/30">
              <TrendingUp size={16} className="text-white" />
            </div>
            <span className="text-sm font-semibold tracking-wide text-white/90">
              TradeMate
            </span>
          </div>

          {/* Brand copy */}
          <div className="relative z-10 flex flex-1 flex-col justify-center px-10 pb-12">
            {/* Badge */}
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-3 py-1">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-violet-400" />
              <span className="text-xs font-medium tracking-wide text-violet-300">
                {badge}
              </span>
            </div>

            {/* Headline */}
            <h1 className="mt-5 text-[2.6rem] font-bold leading-[1.15] text-white">
              {headline.top}
              <br />
              <span className="bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text text-transparent">
                {headline.bottom}
              </span>
            </h1>

            {/* Tagline */}
            <p className="mt-4 max-w-[280px] text-sm leading-relaxed text-zinc-400">
              {tagline}
            </p>

            {/* Features */}
            <ul className="mt-8 space-y-5">
              {features.map(({ Icon, title, desc }) => (
                <li key={title} className="flex items-start gap-3.5">
                  <div className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md border border-violet-500/20 bg-violet-500/10">
                    <Icon size={13} className="text-violet-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white/90">{title}</p>
                    <p className="mt-0.5 text-xs leading-relaxed text-zinc-500">
                      {desc}
                    </p>
                  </div>
                </li>
              ))}
            </ul>

            {/* Stats strip */}
            {stats && stats.length > 0 && (
              <div className="mt-10 flex items-center gap-8 border-t border-white/[0.07] pt-6">
                {stats.map(({ value, label }) => (
                  <div key={label}>
                    <p className="text-lg font-bold text-white">{value}</p>
                    <p className="text-xs text-zinc-500">{label}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </MouseTrackGlow>
      </div>

      {/* ── Right: form panel — full-width on mobile, 45% on desktop ── */}
      <div className="flex flex-1 flex-col overflow-y-auto bg-white dark:bg-zinc-950">
        {children}
      </div>
    </div>
  );
}
