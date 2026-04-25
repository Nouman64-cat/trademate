"use client";

import { useState, useRef } from "react";
import { Check, Pencil, Pin, Trash2, X } from "lucide-react";
import type { Conversation } from "@/types";
import { truncateTitle } from "@/lib/utils";
import { cn } from "@/lib/cn";

interface SidebarItemProps {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onRename: (title: string) => void;
  onPin: () => void;
  onUnpin: () => void;
}

export function SidebarItem({
  conversation,
  isActive,
  onSelect,
  onDelete,
  onRename,
  onPin,
  onUnpin,
}: SidebarItemProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(conversation.title);
  const inputRef = useRef<HTMLInputElement>(null);
  const isPinned = Boolean(conversation.pinnedAt);

  const startEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setDraft(conversation.title);
    setEditing(true);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const commitEdit = () => {
    const trimmed = draft.trim();
    if (trimmed) onRename(trimmed);
    setEditing(false);
  };

  const cancelEdit = () => {
    setDraft(conversation.title);
    setEditing(false);
  };

  return (
    <li>
      <button
        onClick={onSelect}
        className={cn(
          "group w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm transition-colors",
          isActive
            ? "bg-zinc-200/70 dark:bg-zinc-700/60 text-zinc-900 dark:text-zinc-100"
            : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-100"
        )}
      >
        {/* Persistent pin dot for pinned conversations */}
        {isPinned && !editing && (
          <Pin
            size={10}
            className="flex-shrink-0 text-violet-500 dark:text-violet-400 fill-current"
          />
        )}

        {editing ? (
          <input
            ref={inputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitEdit();
              if (e.key === "Escape") cancelEdit();
              e.stopPropagation();
            }}
            onClick={(e) => e.stopPropagation()}
            className="flex-1 bg-transparent outline-none border-b border-zinc-400 dark:border-zinc-500 text-sm min-w-0"
          />
        ) : conversation.titleLoading ? (
          <span className="flex-1 h-3.5 rounded bg-zinc-300 dark:bg-zinc-600 animate-pulse" />
        ) : (
          <span className="flex-1 truncate">{conversation.title}</span>
        )}

        {/* Action icons */}
        <span
          className={cn(
            "flex items-center gap-0.5 flex-shrink-0",
            editing ? "flex" : "hidden group-hover:flex"
          )}
          onClick={(e) => e.stopPropagation()}
        >
          {editing ? (
            <>
              <ActionIcon label="Save" onClick={commitEdit}>
                <Check size={12} />
              </ActionIcon>
              <ActionIcon label="Cancel" onClick={cancelEdit}>
                <X size={12} />
              </ActionIcon>
            </>
          ) : (
            <>
              <ActionIcon label="Rename" onClick={startEdit}>
                <Pencil size={12} />
              </ActionIcon>
              <ActionIcon
                label={isPinned ? "Unpin" : "Pin"}
                onClick={(e) => {
                  e.stopPropagation();
                  isPinned ? onUnpin() : onPin();
                }}
                active={isPinned}
              >
                <Pin size={12} className={isPinned ? "fill-current" : ""} />
              </ActionIcon>
              <ActionIcon label="Delete" onClick={onDelete} danger>
                <Trash2 size={12} />
              </ActionIcon>
            </>
          )}
        </span>
      </button>
    </li>
  );
}

function ActionIcon({
  label,
  onClick,
  danger,
  active,
  children,
}: {
  label: string;
  onClick: (e: React.MouseEvent) => void;
  danger?: boolean;
  active?: boolean;
  children: React.ReactNode;
}) {
  return (
    <span
      role="button"
      aria-label={label}
      onClick={(e) => { e.stopPropagation(); onClick(e); }}
      className={cn(
        "p-1 rounded transition-colors",
        danger
          ? "hover:text-red-500 dark:hover:text-red-400"
          : active
          ? "text-violet-500 dark:text-violet-400 hover:text-violet-700 dark:hover:text-violet-300"
          : "hover:text-zinc-900 dark:hover:text-zinc-100"
      )}
    >
      {children}
    </span>
  );
}
