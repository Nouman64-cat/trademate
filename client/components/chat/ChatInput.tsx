"use client";

import { useRef, useState, type KeyboardEvent, type FormEvent } from "react";
import {
  ArrowUp,
  Loader2,
  Sparkles,
  Paperclip,
  Square,
  X,
} from "lucide-react";
import { useAutoResize } from "@/hooks/useAutoResize";
import { cn } from "@/lib/cn";
import { useAuthStore } from "@/stores/authStore";
import UploadService, { type UploadResult } from "@/services/upload.service";
import { FILE_TYPE_CONFIG, DEFAULT_FILE_CONFIG } from "@/lib/fileTypeConfig";
import dynamic from "next/dynamic";

const VoiceModal = dynamic(
  () => import("./VoiceModal").then((m) => ({ default: m.VoiceModal })),
  { ssr: false }
);

interface ChatInputProps {
  onSend: (message: string) => void;
  isStreaming: boolean;
  onStop?: () => void;
}

export { FILE_TYPE_CONFIG } from "@/lib/fileTypeConfig";

// ── preview cards ─────────────────────────────────────────────────────────────

function DocPreviewCard({
  result,
  onRemove,
}: {
  result: UploadResult;
  onRemove: () => void;
}) {
  const cfg = FILE_TYPE_CONFIG[result.file_type] ?? DEFAULT_FILE_CONFIG;
  const Icon = cfg.icon;

  return (
    <div className="relative inline-flex items-center gap-3 p-2.5 pr-9 rounded-xl border bg-white dark:bg-zinc-800/60 border-zinc-200 dark:border-zinc-700 shadow-sm w-[200px]">
      <button
        type="button"
        onClick={onRemove}
        aria-label="Remove attachment"
        className="absolute top-1.5 right-1.5 h-5 w-5 rounded-full flex items-center justify-center text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors"
      >
        <X size={11} />
      </button>
      <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0", cfg.bg)}>
        <Icon size={19} className={cfg.iconColor} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-zinc-800 dark:text-zinc-100 truncate leading-tight">
          {result.filename}
        </p>
        <p className="text-[10px] text-zinc-400 dark:text-zinc-500 mt-0.5">{cfg.label}</p>
      </div>
    </div>
  );
}

function DocPreviewCardSkeleton({ filename }: { filename: string }) {
  return (
    <div className="inline-flex items-center gap-3 p-2.5 rounded-xl border bg-white dark:bg-zinc-800/60 border-zinc-200 dark:border-zinc-700 shadow-sm w-[200px]">
      <div className="h-10 w-10 rounded-lg bg-zinc-100 dark:bg-zinc-700 flex items-center justify-center flex-shrink-0 animate-pulse">
        <Loader2 size={16} className="animate-spin text-zinc-400 dark:text-zinc-500" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400 truncate leading-tight">
          {filename}
        </p>
        <div className="h-2 w-14 bg-zinc-100 dark:bg-zinc-700 rounded mt-1.5 animate-pulse" />
      </div>
    </div>
  );
}

// ── main component ────────────────────────────────────────────────────────────

interface UploadingEntry { id: number; name: string }

export function ChatInput({ onSend, isStreaming, onStop }: ChatInputProps) {
  const [value, setValue] = useState("");
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [attachedDocs, setAttachedDocs] = useState<UploadResult[]>([]);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingEntry[]>([]);
  const [uploadErrors, setUploadErrors] = useState<string[]>([]);

  const uploadCounter = useRef(0);
  const token = useAuthStore((s) => s.token) ?? "";
  const textareaRef = useAutoResize(value);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isUploading = uploadingFiles.length > 0;
  const canSend =
    (value.trim().length > 0 || attachedDocs.length > 0) && !isStreaming && !isUploading;

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (!files.length) return;
    e.target.value = "";

    await Promise.all(
      files.map(async (file) => {
        const id = ++uploadCounter.current;
        setUploadingFiles((prev) => [...prev, { id, name: file.name }]);
        try {
          const result = await UploadService.uploadDocument(file, token);
          setAttachedDocs((prev) => [...prev, result]);
        } catch (err) {
          const msg = err instanceof Error ? err.message : `Failed to upload ${file.name}`;
          setUploadErrors((prev) => [...prev, msg]);
        } finally {
          setUploadingFiles((prev) => prev.filter((f) => f.id !== id));
        }
      })
    );
  };

  const removeDoc = (index: number) =>
    setAttachedDocs((prev) => prev.filter((_, i) => i !== index));

  const removeError = (index: number) =>
    setUploadErrors((prev) => prev.filter((_, i) => i !== index));

  const handleSubmit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!canSend) return;

    let finalMessage = value.trim();

    if (attachedDocs.length > 0) {
      const docSections = attachedDocs
        .map((d) => `[Attached document: ${d.filename}]\n\n${d.text.slice(0, 60_000)}`)
        .join("\n\n");
      const question =
        finalMessage ||
        (attachedDocs.length === 1
          ? "Please analyze this document."
          : "Please analyze these documents.");
      finalMessage = `${docSections}\n\n---\n\n${question}`;
      setAttachedDocs([]);
    }

    onSend(finalMessage);
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const showPreview = isUploading || attachedDocs.length > 0 || uploadErrors.length > 0;

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
          {/* Document preview area */}
          {showPreview && (
            <div className="px-3 pt-3 flex flex-wrap gap-2">
              {uploadingFiles.map((f) => (
                <DocPreviewCardSkeleton key={f.id} filename={f.name} />
              ))}
              {attachedDocs.map((doc, i) => (
                <DocPreviewCard key={i} result={doc} onRemove={() => removeDoc(i)} />
              ))}
              {uploadErrors.map((err, i) => (
                <div
                  key={i}
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-xs text-red-600 dark:text-red-400"
                >
                  <span className="truncate max-w-[160px]">{err}</span>
                  <button
                    type="button"
                    onClick={() => removeError(i)}
                    className="hover:text-red-800 dark:hover:text-red-200 transition-colors flex-shrink-0"
                  >
                    <X size={11} />
                  </button>
                </div>
              ))}
            </div>
          )}

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
            <div className="flex items-center gap-1">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.pptx,.xlsx,.xls"
                multiple
                className="hidden"
                onChange={handleFileChange}
              />
              <button
                type="button"
                aria-label="Attach documents"
                disabled={isStreaming}
                onClick={() => fileInputRef.current?.click()}
                className={cn(
                  "h-8 w-8 rounded-lg inline-flex items-center justify-center transition-colors",
                  attachedDocs.length > 0
                    ? "text-violet-500 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/30"
                    : "text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700",
                  isStreaming && "opacity-40 cursor-not-allowed"
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
                  "hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors"
                )}
              >
                <Sparkles size={16} />
              </button>
            </div>

            {isStreaming ? (
              <button
                type="button"
                onClick={onStop}
                aria-label="Stop generating"
                className={cn(
                  "h-8 w-8 rounded-lg inline-flex items-center justify-center",
                  "bg-zinc-800 dark:bg-zinc-200 text-white dark:text-zinc-900",
                  "hover:bg-zinc-700 dark:hover:bg-zinc-300 transition-colors"
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
