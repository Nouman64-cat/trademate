"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { TrendingUp } from "lucide-react";
import ShareService, { type SharedConversation } from "@/services/share.service";
import { FILE_TYPE_CONFIG, DEFAULT_FILE_CONFIG } from "@/lib/fileTypeConfig";
import { MarkdownRenderer } from "@/components/chat/MarkdownRenderer";
import { cn } from "@/lib/cn";

const DOC_SEP = "\n\n---\n\n";

function parseDocMessage(content: string) {
  if (!content.startsWith("[Attached document:")) return null;
  const sepIdx = content.lastIndexOf(DOC_SEP);
  if (sepIdx === -1) return null;
  const question = content.slice(sepIdx + DOC_SEP.length).trim();
  const docSection = content.slice(0, sepIdx);
  const filenames = [...docSection.matchAll(/^\[Attached document: (.+?)\]/gm)].map((m) => m[1]);
  if (filenames.length === 0) return null;
  return { filenames, question };
}

function DocCard({ filename }: { filename: string }) {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  const cfg = FILE_TYPE_CONFIG[ext] ?? DEFAULT_FILE_CONFIG;
  const Icon = cfg.icon;
  return (
    <div className="inline-flex items-center gap-3 p-2.5 rounded-xl border bg-white/60 dark:bg-zinc-700/40 border-zinc-200 dark:border-zinc-600 w-[200px]">
      <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0", cfg.bg)}>
        <Icon size={19} className={cfg.iconColor} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-zinc-800 dark:text-zinc-100 truncate leading-tight">{filename}</p>
        <p className="text-[10px] text-zinc-400 dark:text-zinc-500 mt-0.5">{cfg.label}</p>
      </div>
    </div>
  );
}

export default function SharedConversationPage() {
  const { token } = useParams<{ token: string }>();
  const router = useRouter();
  const [data, setData] = useState<SharedConversation | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    ShareService.fetchShared(token)
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 h-14 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center">
            <TrendingUp size={14} className="text-white" />
          </div>
          <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">TradeMate</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => router.push("/auth/login")}
            className="px-3 py-1.5 text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
          >
            Log in
          </button>
          <button
            onClick={() => router.push("/auth/register")}
            className="px-3 py-1.5 text-sm rounded-lg bg-violet-600 hover:bg-violet-700 text-white font-medium transition-colors"
          >
            Sign up
          </button>
        </div>
      </header>

      {/* Body */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-8">
          {loading && (
            <div className="flex justify-center py-20">
              <div className="flex gap-1.5">
                {[0, 150, 300].map((d) => (
                  <span
                    key={d}
                    className="h-2.5 w-2.5 rounded-full bg-violet-400 animate-bounce"
                    style={{ animationDelay: `${d}ms` }}
                  />
                ))}
              </div>
            </div>
          )}

          {error && !loading && (
            <div className="text-center py-20">
              <p className="text-zinc-500 dark:text-zinc-400 text-sm">
                This shared conversation could not be found or the link has expired.
              </p>
            </div>
          )}

          {data && (
            <>
              {data.title && (
                <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100 mb-6">
                  {data.title}
                </h1>
              )}
              <div className="space-y-1">
                {data.messages.map((msg) => {
                  const parsed = msg.role === "user" ? parseDocMessage(msg.content) : null;
                  const defaultQ =
                    parsed && parsed.filenames.length > 1
                      ? "Please analyze these documents."
                      : "Please analyze this document.";

                  if (msg.role === "user") {
                    return (
                      <div key={msg.id} className="flex flex-col items-end px-0 py-1 gap-1.5">
                        {parsed && (
                          <div className="flex flex-wrap gap-2 justify-end">
                            {parsed.filenames.map((name) => (
                              <DocCard key={name} filename={name} />
                            ))}
                          </div>
                        )}
                        <div className="max-w-[75%] px-4 py-3 rounded-2xl rounded-tr-sm bg-zinc-200 dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100 text-sm leading-7">
                          {parsed ? (
                            parsed.question === defaultQ ? (
                              <span className="text-zinc-500 dark:text-zinc-400 italic text-xs">{defaultQ}</span>
                            ) : (
                              parsed.question
                            )
                          ) : (
                            msg.content
                          )}
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div key={msg.id} className="px-0 py-3">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="h-6 w-6 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
                          <span className="text-white text-[10px] font-bold">TM</span>
                        </div>
                        <span className="text-xs font-semibold text-zinc-600 dark:text-zinc-400">TradeMate</span>
                      </div>
                      <div className="pl-8">
                        <MarkdownRenderer content={msg.content} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </main>

      {/* Footer CTA */}
      {data && (
        <div className="border-t border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm px-6 py-4">
          <div className="max-w-3xl mx-auto flex items-center justify-between gap-4">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Want to ask your own trade questions?
            </p>
            <button
              onClick={() => router.push("/auth/register")}
              className="flex-shrink-0 px-4 py-2 text-sm rounded-lg bg-violet-600 hover:bg-violet-700 text-white font-medium transition-colors"
            >
              Try TradeMate free
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
