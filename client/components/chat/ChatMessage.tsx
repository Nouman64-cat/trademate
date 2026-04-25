"use client";

import { useState } from "react";
import { Copy, Check, RotateCcw } from "lucide-react";
import dynamic from "next/dynamic";
import type { Message } from "@/types";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { StarRating } from "./StarRating";
import { IconButton } from "@/components/ui/IconButton";
import { FILE_TYPE_CONFIG, DEFAULT_FILE_CONFIG } from "@/lib/fileTypeConfig";
import { useChatStore } from "@/stores/chatStore";
import MessageService from "@/services/message.service";
import { cn } from "@/lib/cn";

// Leaflet accesses window/document at import time — must be client-only
const RouteWidget = dynamic(
  () => import("./RouteWidget").then((m) => ({ default: m.RouteWidget })),
  { ssr: false }
);

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
}

// ── document message parser ───────────────────────────────────────────────────

interface ParsedDocMessage {
  filenames: string[];
  question: string;
}

const DOC_SEP = "\n\n---\n\n";

function parseDocMessage(content: string): ParsedDocMessage | null {
  if (!content.startsWith("[Attached document:")) return null;

  const sepIdx = content.lastIndexOf(DOC_SEP);
  if (sepIdx === -1) return null;

  const question = content.slice(sepIdx + DOC_SEP.length).trim();
  const docSection = content.slice(0, sepIdx);
  const filenames = [...docSection.matchAll(/^\[Attached document: (.+?)\]/gm)].map(
    (m) => m[1]
  );

  if (filenames.length === 0) return null;
  return { filenames, question };
}

function extFromFilename(filename: string): string {
  return filename.split(".").pop()?.toLowerCase() ?? "";
}

function DocMessageCard({ filename }: { filename: string }) {
  const ext = extFromFilename(filename);
  const cfg = FILE_TYPE_CONFIG[ext] ?? DEFAULT_FILE_CONFIG;
  const Icon = cfg.icon;

  return (
    <div className="inline-flex items-center gap-3 p-2.5 rounded-xl border bg-white/60 dark:bg-zinc-700/40 border-zinc-200 dark:border-zinc-600 w-[200px]">
      <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0", cfg.bg)}>
        <Icon size={19} className={cfg.iconColor} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-zinc-800 dark:text-zinc-100 truncate leading-tight">
          {filename}
        </p>
        <p className="text-[10px] text-zinc-400 dark:text-zinc-500 mt-0.5">{cfg.label}</p>
      </div>
    </div>
  );
}

export function ChatMessage({ message, isStreaming }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const isAssistant = message.role === "assistant";
  const activeConversationId = useChatStore((s) => s.activeConversationId);
  const setMessageRating = useChatStore((s) => s.setMessageRating);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRate = async (rating: number) => {
    if (!message.dbId || !activeConversationId) return;
    // Optimistic update, rolled back on failure
    const previous = message.rating ?? null;
    setMessageRating(activeConversationId, message.dbId, rating);
    try {
      await MessageService.rateMessage(message.dbId, rating);
    } catch (err) {
      setMessageRating(activeConversationId, message.dbId, previous ?? 0);
      throw err;
    }
  };

  if (message.role === "user") {
    const parsed = parseDocMessage(message.content);
    const defaultQuestion =
      parsed && parsed.filenames.length > 1
        ? "Please analyze these documents."
        : "Please analyze this document.";

    return (
      <div className="flex flex-col items-end px-4 py-1 group gap-1.5">
        {parsed && (
          <div className="flex flex-wrap gap-2 justify-end">
            {parsed.filenames.map((name) => (
              <DocMessageCard key={name} filename={name} />
            ))}
          </div>
        )}
        <div
          className={cn(
            "max-w-[75%] px-4 py-3 rounded-2xl rounded-tr-sm",
            "bg-zinc-200 dark:bg-zinc-700",
            "text-zinc-900 dark:text-zinc-100 text-sm leading-7"
          )}
        >
          {parsed ? (
            parsed.question === defaultQuestion ? (
              <span className="text-zinc-500 dark:text-zinc-400 italic text-xs">
                {defaultQuestion}
              </span>
            ) : (
              parsed.question
            )
          ) : (
            message.content
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-3 group">
      {/* Avatar + name */}
      <div className="flex items-center gap-2 mb-0">
        <div className="h-6 w-6 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
          <span className="text-white text-[10px] font-bold">TM</span>
        </div>
      </div>

      {/* Content */}
      <div className="pl-8 -mt-6">
        {message.content ? (
          <MarkdownRenderer content={message.content} />
        ) : (
          <StreamingCursor />
        )}

        {/* Streaming cursor appended while streaming */}
        {isStreaming && message.content && <StreamingCursor inline />}

        {/* Inline route widgets — one per evaluate_shipping_routes tool call */}
        {!isStreaming && message.widgets?.map((w, i) =>
          w.type === "route_evaluation" ? (
            <RouteWidget key={i} data={w.data} />
          ) : null
        )}

        {/* Action bar — visible on hover when not streaming */}
        {!isStreaming && message.content && (
          <div
            className={cn(
              "flex items-center gap-2 mt-2 transition-opacity",
              // Keep a submitted rating visible; otherwise only show on hover.
              message.rating
                ? "opacity-100"
                : "opacity-0 group-hover:opacity-100 focus-within:opacity-100"
            )}
          >
            <IconButton label="Copy" size="sm" onClick={handleCopy}>
              {copied ? <Check size={13} /> : <Copy size={13} />}
            </IconButton>
            <IconButton label="Regenerate" size="sm">
              <RotateCcw size={13} />
            </IconButton>
            {isAssistant && (
              <div className="ml-1 pl-2 border-l border-zinc-200 dark:border-zinc-700">
                <StarRating
                  value={message.rating ?? null}
                  onSubmit={handleRate}
                  disabled={!message.dbId}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StreamingCursor({ inline }: { inline?: boolean }) {
  if (inline) {
    return (
      <span className="inline-block w-0.5 h-4 bg-zinc-600 dark:bg-zinc-300 animate-pulse ml-0.5 align-middle" />
    );
  }
  return (
    <div className="flex items-center gap-1 mt-1">
      <span className="h-2 w-2 rounded-full bg-zinc-400 dark:bg-zinc-500 animate-bounce [animation-delay:0ms]" />
      <span className="h-2 w-2 rounded-full bg-zinc-400 dark:bg-zinc-500 animate-bounce [animation-delay:150ms]" />
      <span className="h-2 w-2 rounded-full bg-zinc-400 dark:bg-zinc-500 animate-bounce [animation-delay:300ms]" />
    </div>
  );
}
