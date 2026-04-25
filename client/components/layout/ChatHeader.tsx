"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Check,
  Download,
  Menu,
  MoreHorizontal,
  Pencil,
  Share2,
  Trash2,
  X,
} from "lucide-react";
import { ModelSelector } from "@/components/ui/ModelSelector";
import { IconButton } from "@/components/ui/IconButton";
import { useUIStore } from "@/stores/uiStore";
import { useChatStore } from "@/stores/chatStore";
import ShareService from "@/services/share.service";
import { cn } from "@/lib/cn";

export function ChatHeader() {
  const router = useRouter();
  const { toggleMobileSidebar, toggleDesktopSidebar } = useUIStore();
  const { getActiveConversation, deleteConversation, renameConversation, activeConversationId } =
    useChatStore();

  // Share
  const [copied, setCopied] = useState(false);

  // Three-dots dropdown
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Rename modal
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const renameInputRef = useRef<HTMLInputElement>(null);

  // Close menu on outside click
  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [menuOpen]);

  // Focus rename input when modal opens
  useEffect(() => {
    if (renaming) setTimeout(() => renameInputRef.current?.focus(), 50);
  }, [renaming]);

  const handleToggleSidebar = () => {
    if (typeof window !== "undefined" && window.innerWidth >= 1024) {
      toggleDesktopSidebar();
    } else {
      toggleMobileSidebar();
    }
  };

  const handleShare = async () => {
    if (!activeConversationId) return;
    try {
      const token = await ShareService.createShareLink(activeConversationId);
      const shareUrl = `${window.location.origin}/share/${token}`;
      await navigator.clipboard.writeText(shareUrl).catch(() => {
        const input = document.createElement("input");
        input.value = shareUrl;
        document.body.appendChild(input);
        input.select();
        document.execCommand("copy");
        document.body.removeChild(input);
      });
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // silently fail — user may retry
    }
  };

  const handleRenameOpen = () => {
    const conv = getActiveConversation();
    if (!conv) return;
    setRenameValue(conv.title);
    setMenuOpen(false);
    setRenaming(true);
  };

  const handleRenameCommit = () => {
    const trimmed = renameValue.trim();
    if (trimmed && activeConversationId) {
      renameConversation(activeConversationId, trimmed);
    }
    setRenaming(false);
  };

  const handleExport = () => {
    const conv = getActiveConversation();
    if (!conv) return;
    setMenuOpen(false);
    const lines = conv.messages.map(
      (m) => `${m.role === "user" ? "You" : "TradeMate"}: ${m.content}`
    );
    const blob = new Blob([lines.join("\n\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${conv.title}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDelete = () => {
    if (!activeConversationId) return;
    setMenuOpen(false);
    deleteConversation(activeConversationId);
    router.push("/chat");
  };

  const activeConversation = getActiveConversation();
  const hasMessages = (activeConversation?.messages.length ?? 0) > 0;
  const hasConversation = Boolean(activeConversationId);

  return (
    <>
      <header className="flex items-center justify-between px-4 h-14 border-b border-zinc-200 dark:border-zinc-800 flex-shrink-0 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <button
            onClick={handleToggleSidebar}
            aria-label="Toggle sidebar"
            className="h-8 w-8 rounded-lg inline-flex items-center justify-center text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <Menu size={18} />
          </button>
          <ModelSelector />
        </div>

        <div className="flex items-center gap-1">
          {/* Share — copy link */}
          {hasMessages && (
            <IconButton
              label={copied ? "Link copied!" : "Share conversation"}
              onClick={handleShare}
              className={cn(copied && "text-emerald-500 dark:text-emerald-400")}
            >
              {copied ? <Check size={16} /> : <Share2 size={16} />}
            </IconButton>
          )}

          {/* Three-dots dropdown */}
          <div className="relative" ref={menuRef}>
            <IconButton
              label="More options"
              onClick={() => setMenuOpen((o) => !o)}
              className={cn(menuOpen && "bg-zinc-100 dark:bg-zinc-700 text-zinc-800 dark:text-zinc-100")}
            >
              <MoreHorizontal size={16} />
            </IconButton>

            {menuOpen && (
              <div className="absolute right-0 top-full mt-1.5 w-48 rounded-xl bg-white dark:bg-zinc-800 border border-zinc-100 dark:border-zinc-700 shadow-lg z-50 py-1 overflow-hidden">
                <DropdownItem
                  icon={<Pencil size={13} />}
                  disabled={!hasConversation}
                  onClick={handleRenameOpen}
                >
                  Rename conversation
                </DropdownItem>
                <DropdownItem
                  icon={<Download size={13} />}
                  disabled={!hasConversation}
                  onClick={handleExport}
                >
                  Export as text
                </DropdownItem>
                <div className="my-1 border-t border-zinc-100 dark:border-zinc-700" />
                <DropdownItem
                  icon={<Trash2 size={13} />}
                  disabled={!hasConversation}
                  onClick={handleDelete}
                  danger
                >
                  Delete conversation
                </DropdownItem>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Rename modal */}
      {renaming && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
          onClick={(e) => { if (e.target === e.currentTarget) setRenaming(false); }}
        >
          <div className="bg-white dark:bg-zinc-800 rounded-2xl shadow-xl border border-zinc-200 dark:border-zinc-700 w-full max-w-sm mx-4 p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Rename conversation
              </h3>
              <button
                onClick={() => setRenaming(false)}
                className="h-6 w-6 rounded-md flex items-center justify-center text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors"
              >
                <X size={14} />
              </button>
            </div>
            <input
              ref={renameInputRef}
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleRenameCommit();
                if (e.key === "Escape") setRenaming(false);
              }}
              className={cn(
                "w-full rounded-lg border border-zinc-200 dark:border-zinc-600",
                "bg-zinc-50 dark:bg-zinc-700/50 px-3 py-2 text-sm",
                "text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400",
                "focus:outline-none focus:ring-2 focus:ring-violet-500/40 focus:border-violet-400"
              )}
              placeholder="Conversation title"
            />
            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => setRenaming(false)}
                className="px-3 py-1.5 text-sm rounded-lg text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRenameCommit}
                disabled={!renameValue.trim()}
                className="px-3 py-1.5 text-sm rounded-lg bg-violet-600 hover:bg-violet-700 text-white font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function DropdownItem({
  icon,
  children,
  onClick,
  disabled,
  danger,
}: {
  icon: React.ReactNode;
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  danger?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "w-full flex items-center gap-2.5 px-3 py-2 text-sm transition-colors text-left",
        danger
          ? "text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30"
          : "text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-700/50",
        disabled && "opacity-40 cursor-not-allowed pointer-events-none"
      )}
    >
      <span className="flex-shrink-0">{icon}</span>
      {children}
    </button>
  );
}
