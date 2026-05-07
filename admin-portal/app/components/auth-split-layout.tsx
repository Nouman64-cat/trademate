'use client';

import * as React from 'react';
import { ShieldCheck } from 'lucide-react';
import { MouseTrackGlow } from './mouse-track-glow';

export interface AdminAuthFeature {
  Icon: React.ComponentType<{ size?: number; className?: string }>;
  title: string;
  desc: string;
}

export interface AdminAuthStat {
  value: string;
  label: string;
}

export interface AuthSplitLayoutProps {
  badge: string;
  headline: { top: string; bottom: string };
  tagline: string;
  features: AdminAuthFeature[];
  stats: AdminAuthStat[];
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
    <div className="fixed inset-0 z-50 flex bg-white dark:bg-gray-950">
      {/* ── Left: interactive brand panel — desktop only ── */}
      <div className="hidden lg:flex lg:w-[55%] xl:w-[58%]">
        <MouseTrackGlow className="flex flex-1 flex-col bg-gradient-to-br from-slate-950 via-[#030f2c] to-blue-950">
          {/* Grid texture */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage:
                'linear-gradient(rgba(255,255,255,0.7) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.7) 1px, transparent 1px)',
              backgroundSize: '52px 52px',
            }}
          />

          {/* Static corner accent */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full"
            style={{ background: 'rgba(37,99,235,0.1)', filter: 'blur(80px)' }}
          />

          {/* Logo */}
          <div className="relative z-10 flex items-center gap-2.5 p-8">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 shadow-lg shadow-blue-500/30">
              <ShieldCheck size={16} className="text-white" />
            </div>
            <span className="text-sm font-semibold tracking-wide text-white/90">
              TradeMate Admin
            </span>
          </div>

          {/* Brand copy */}
          <div className="relative z-10 flex flex-1 flex-col justify-center px-10 pb-12">
            {/* Badge */}
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-400" />
              <span className="text-xs font-medium tracking-wide text-blue-300">
                {badge}
              </span>
            </div>

            {/* Headline */}
            <h1 className="mt-5 text-[2.6rem] font-bold leading-[1.15] text-white">
              {headline.top}
              <br />
              <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                {headline.bottom}
              </span>
            </h1>

            {/* Tagline */}
            <p className="mt-4 max-w-[280px] text-sm leading-relaxed text-slate-400">
              {tagline}
            </p>

            {/* Features */}
            <ul className="mt-8 space-y-5">
              {features.map(({ Icon, title, desc }) => (
                <li key={title} className="flex items-start gap-3.5">
                  <div className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md border border-blue-500/20 bg-blue-500/10">
                    <Icon size={13} className="text-blue-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white/90">{title}</p>
                    <p className="mt-0.5 text-xs leading-relaxed text-slate-500">
                      {desc}
                    </p>
                  </div>
                </li>
              ))}
            </ul>

            {/* Stats strip */}
            <div
              className="mt-10 flex items-center gap-8 pt-6"
              style={{ borderTop: '1px solid rgba(255,255,255,0.07)' }}
            >
              {stats.map(({ value, label }) => (
                <div key={label}>
                  <p className="text-lg font-bold text-white">{value}</p>
                  <p className="text-xs text-slate-500">{label}</p>
                </div>
              ))}
            </div>
          </div>
        </MouseTrackGlow>
      </div>

      {/* ── Right: form panel — full-width on mobile, 45% on desktop ── */}
      <div className="flex flex-1 flex-col overflow-y-auto bg-white dark:bg-gray-950">
        {children}
      </div>
    </div>
  );
}
