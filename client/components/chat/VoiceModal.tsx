"use client";

import { useEffect, useRef } from "react";
import { MicOff, X } from "lucide-react";
import { useVoice, type VoiceStatus } from "@/hooks/useVoice";
import { cn } from "@/lib/cn";

// ── Types ─────────────────────────────────────────────────────────────────────

interface VoiceModalProps {
  token: string;
  onClose: () => void;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const STATUS_LABELS: Record<VoiceStatus, string> = {
  idle: "Ready",
  connecting: "Connecting…",
  active: "Listening",
  ended: "Session ended",
};

function formatTime(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

// ── Waveform ─────────────────────────────────────────────────────────────────

/** Five animated bars that pulse when the session is active. */
function Waveform({ active }: { active: boolean }) {
  const barHeights = [40, 70, 55, 80, 45];
  return (
    <div className="flex items-center justify-center gap-1.5 h-14">
      {barHeights.map((pct, i) => (
        <span
          key={i}
          style={
            active
              ? ({
                  "--bar-height": `${pct}%`,
                  animationDelay: `${i * 110}ms`,
                } as React.CSSProperties)
              : undefined
          }
          className={cn(
            "w-1.5 rounded-full bg-violet-500 transition-all duration-300",
            active ? "animate-voice-bar" : "h-[20%]"
          )}
        />
      ))}
    </div>
  );
}

// ── VoiceModal ────────────────────────────────────────────────────────────────

export function VoiceModal({ token, onClose }: VoiceModalProps) {
  const { state, start, stop } = useVoice(token);
  const transcriptRef = useRef<HTMLDivElement>(null);

  // Auto-start when the modal mounts; stop on unmount.
  // start() self-cancels if stop() runs concurrently (handles React StrictMode).
  useEffect(() => {
    start();
    return () => stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-scroll transcript to latest entry
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [state.transcript]);

  const handleClose = () => {
    stop();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Voice conversation"
        className={cn(
          "relative w-full max-w-sm mx-4 rounded-3xl",
          "bg-white dark:bg-zinc-900",
          "shadow-2xl border border-zinc-100 dark:border-zinc-800",
          "flex flex-col items-center p-8 gap-5"
        )}
      >
        {/* Close (X) button */}
        <button
          onClick={handleClose}
          aria-label="Close voice conversation"
          className={cn(
            "absolute top-4 right-4 h-8 w-8 rounded-full",
            "flex items-center justify-center",
            "text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300",
            "hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          )}
        >
          <X size={16} />
        </button>

        {/* Avatar */}
        <div className="h-16 w-16 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg">
          <span className="text-white text-xl font-bold select-none">TM</span>
        </div>

        {/* Title + status */}
        <div className="text-center -mt-1">
          <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
            Voice Conversation
          </h2>
          <p
            className={cn(
              "text-sm mt-1",
              state.status === "active"
                ? "text-violet-500"
                : "text-zinc-400 dark:text-zinc-500"
            )}
          >
            {STATUS_LABELS[state.status]}
          </p>
        </div>

        {/* Animated waveform */}
        <Waveform active={state.status === "active"} />

        {/* Elapsed / total timer */}
        {(state.status === "active" || state.status === "ended") && (
          <div className="flex items-baseline gap-1 -mt-2">
            <span className="text-2xl font-mono font-semibold text-zinc-900 dark:text-zinc-100">
              {formatTime(state.elapsedSeconds)}
            </span>
            <span className="text-sm text-zinc-400 dark:text-zinc-500">/ 1:00</span>
          </div>
        )}

        {/* Tool activity indicator */}
        {state.toolActivity && (
          <div className="flex items-center gap-2 text-sm text-violet-500 -mt-2">
            <span className="inline-block h-2 w-2 rounded-full bg-violet-500 animate-pulse" />
            {state.toolActivity}
          </div>
        )}

        {/* Error notice */}
        {state.error && (
          <p className="text-sm text-red-500 text-center px-2">{state.error}</p>
        )}

        {/* Live transcript */}
        {state.transcript && (
          <div
            ref={transcriptRef}
            className={cn(
              "w-full max-h-36 overflow-y-auto rounded-2xl p-3",
              "bg-zinc-50 dark:bg-zinc-800",
              "text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed whitespace-pre-wrap"
            )}
          >
            {state.transcript}
          </div>
        )}

        {/* Action button */}
        {state.status !== "ended" ? (
          <button
            onClick={handleClose}
            aria-label="End session"
            className={cn(
              "h-14 w-14 rounded-full flex items-center justify-center",
              "bg-red-500 hover:bg-red-600 active:bg-red-700",
              "text-white shadow-lg transition-colors"
            )}
          >
            <MicOff size={22} />
          </button>
        ) : (
          <button
            onClick={onClose}
            className={cn(
              "px-6 py-2.5 rounded-xl font-medium text-sm",
              "bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900",
              "hover:bg-zinc-700 dark:hover:bg-zinc-300 transition-colors"
            )}
          >
            Close
          </button>
        )}
      </div>
    </div>
  );
}
