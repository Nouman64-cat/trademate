"use client";

import { useState, type KeyboardEvent, type FormEvent } from "react";
import { ArrowUp, Square, Paperclip, Mic } from "lucide-react";
import { useAutoResize } from "@/hooks/useAutoResize";
import { cn } from "@/lib/cn";
import { useAuthStore } from "@/stores/authStore";
import dynamic from "next/dynamic";

// VoiceModal uses Web Audio API — must be client-only
const VoiceModal = dynamic(
  () => import("./VoiceModal").then((m) => ({ default: m.VoiceModal })),
  { ssr: false }
);

interface ChatInputProps {
  onSend: (message: string) => void;
  isStreaming: boolean;
  onStop?: () => void;
}

export function ChatInput({ onSend, isStreaming, onStop }: ChatInputProps) {
  const [value, setValue] = useState("");
  const [voiceOpen, setVoiceOpen] = useState(false);
  const token = useAuthStore((s) => s.token) ?? "";
  const textareaRef = useAutoResize(value);

  const canSend = value.trim().length > 0 && !isStreaming;

  const handleSubmit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!canSend) return;
    onSend(value.trim());
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="px-4 pb-4 pt-2">
      <div className="mx-auto max-w-3xl">
        <form
          onSubmit={handleSubmit}
          className={cn(
            "relative flex flex-col rounded-2xl border",
            "bg-white dark:bg-zinc-800",
            "border-zinc-200 dark:border-zinc-700",
            "shadow-sm hover:shadow-md transition-shadow",
            "focus-within:border-zinc-400 dark:focus-within:border-zinc-500"
          )}
        >
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message TradeMate..."
            rows={1}
            className={cn(
              "w-full resize-none bg-transparent px-4 pt-3.5 pb-2",
              "text-sm text-zinc-900 dark:text-zinc-100",
              "placeholder:text-zinc-400 dark:placeholder:text-zinc-500",
              "focus:outline-none",
              "max-h-52 overflow-y-auto"
            )}
          />

          {/* Bottom toolbar */}
          <div className="flex items-center justify-between px-3 pb-3 pt-1">
            {/* Left actions */}
            <div className="flex items-center gap-1">
              <button
                type="button"
                aria-label="Attach file"
                className={cn(
                  "h-8 w-8 rounded-lg inline-flex items-center justify-center",
                  "text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300",
                  "hover:bg-zinc-100 dark:hover:bg-zinc-700",
                  "transition-colors"
                )}
              >
                <Paperclip size={16} />
              </button>
              <button
                type="button"
                aria-label="Voice conversation"
                onClick={() => setVoiceOpen(true)}
                className={cn(
                  "h-8 w-8 rounded-lg inline-flex items-center justify-center",
                  "text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300",
                  "hover:bg-zinc-100 dark:hover:bg-zinc-700",
                  "transition-colors"
                )}
              >
                <Mic size={16} />
              </button>
            </div>

            {/* Send / Stop button */}
            {isStreaming ? (
              <button
                type="button"
                onClick={onStop}
                aria-label="Stop generating"
                className={cn(
                  "h-8 w-8 rounded-lg inline-flex items-center justify-center",
                  "bg-zinc-800 dark:bg-zinc-200 text-white dark:text-zinc-900",
                  "hover:bg-zinc-700 dark:hover:bg-zinc-300",
                  "transition-colors"
                )}
              >
                <Square size={14} fill="currentColor" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!canSend}
                aria-label="Send message"
                className={cn(
                  "h-8 w-8 rounded-lg inline-flex items-center justify-center transition-colors",
                  canSend
                    ? "bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 hover:bg-zinc-700 dark:hover:bg-zinc-300"
                    : "bg-zinc-100 dark:bg-zinc-700 text-zinc-400 dark:text-zinc-500 cursor-not-allowed"
                )}
              >
                <ArrowUp size={16} />
              </button>
            )}
          </div>
        </form>

        <p className="text-center text-[11px] text-zinc-400 dark:text-zinc-600 mt-2">
          TradeMate can make mistakes. Verify important financial information.
        </p>
      </div>

      {voiceOpen && (
        <VoiceModal token={token} onClose={() => setVoiceOpen(false)} />
      )}
    </div>
  );
}
