"use client";

import { useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { LogOut, Pin, Search, SquarePen, TrendingUp, X } from "lucide-react";
import { useChatStore } from "@/stores/chatStore";
import { useAuthStore } from "@/stores/authStore";
import { useLogout } from "@/hooks/useAuth";
import { useUIStore } from "@/stores/uiStore";
import { groupConversationsByDate } from "@/lib/utils";
import { SidebarItem } from "./SidebarItem";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { cn } from "@/lib/cn";

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState("");

  const {
    conversations,
    activeConversationId,
    createConversation,
    deleteConversation,
    setActiveConversation,
    renameConversation,
    pinConversation,
    unpinConversation,
  } = useChatStore();

  const { user } = useAuthStore();
  const logout = useLogout();
  const { mobileSidebarOpen, desktopSidebarCollapsed, setMobileSidebarOpen } = useUIStore();

  const handleNewChat = () => {
    const id = createConversation();
    router.push(`/chat/${id}`);
  };

  const handleSelect = (id: string) => {
    setActiveConversation(id);
    setMobileSidebarOpen(false);
    router.push(`/chat/${id}`);
  };

  // ── filter + split ──────────────────────────────────────────────────────────
  const query = searchQuery.toLowerCase().trim();

  const pinned = conversations
    .filter((c) => c.pinnedAt)
    .sort((a, b) => (b.pinnedAt!.getTime() - a.pinnedAt!.getTime()));

  const unpinned = conversations.filter((c) => !c.pinnedAt);

  const filteredPinned = query
    ? pinned.filter((c) => c.title.toLowerCase().includes(query))
    : pinned;

  const filteredUnpinned = query
    ? unpinned.filter((c) => c.title.toLowerCase().includes(query))
    : unpinned;

  // When searching, show a flat list. Otherwise keep date groups.
  const groups = query ? null : groupConversationsByDate(filteredUnpinned);

  const totalVisible = filteredPinned.length + filteredUnpinned.length;

  return (
    <>
      {/* Mobile backdrop */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 transition-transform duration-300",
          mobileSidebarOpen ? "translate-x-0" : "-translate-x-full",
          "lg:relative lg:translate-x-0 lg:transition-[width] lg:duration-200 lg:overflow-hidden",
          desktopSidebarCollapsed ? "lg:w-0" : "lg:w-64",
          "flex flex-col h-full w-64 flex-shrink-0",
          "bg-zinc-50 dark:bg-zinc-900",
          "border-r border-zinc-200 dark:border-zinc-800",
          className
        )}
      >
        {/* Brand */}
        <div className="flex items-center justify-between px-4 pt-5 pb-3">
          <button
            onClick={() => setMobileSidebarOpen(false)}
            aria-label="Close sidebar"
            className={cn(
              "lg:hidden absolute top-3 right-3",
              "h-7 w-7 rounded-lg inline-flex items-center justify-center",
              "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-100",
              "hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
            )}
          >
            <X size={15} />
          </button>
          <div className="flex items-center gap-2.5">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
              <TrendingUp size={14} className="text-white" />
            </div>
            <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              TradeMate
            </span>
          </div>
          <button
            onClick={handleNewChat}
            aria-label="New chat"
            title="New chat"
            className={cn(
              "h-7 w-7 rounded-lg inline-flex items-center justify-center",
              "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-100",
              "hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
            )}
          >
            <SquarePen size={15} />
          </button>
        </div>

        {/* Search */}
        <div className="px-3 mb-2 relative">
          <Search
            size={13}
            className="absolute left-6 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none"
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search chats…"
            className={cn(
              "w-full h-8 rounded-lg pl-8 pr-7 text-sm",
              "bg-zinc-100 dark:bg-zinc-800",
              "text-zinc-800 dark:text-zinc-200 placeholder:text-zinc-400",
              "focus:outline-none focus:ring-1 focus:ring-violet-500/40"
            )}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              aria-label="Clear search"
              className="absolute right-6 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 transition-colors"
            >
              <X size={12} />
            </button>
          )}
        </div>


        {/* Conversation list */}
        <nav className="flex-1 overflow-y-auto px-2 pb-2">
          {conversations.length === 0 ? (
            <p className="text-xs text-zinc-400 dark:text-zinc-600 text-center mt-8 px-4">
              No conversations yet.
              <br />
              Start a new chat above.
            </p>
          ) : query && totalVisible === 0 ? (
            <p className="text-xs text-zinc-400 dark:text-zinc-600 text-center mt-8 px-4">
              No chats match "{searchQuery}".
            </p>
          ) : (
            <>
              {/* Pinned section */}
              {filteredPinned.length > 0 && (
                <div className="mb-3">
                  <p className="flex items-center gap-1.5 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-600">
                    <Pin size={9} className="fill-current" />
                    Pinned
                  </p>
                  <ul className="space-y-0.5">
                    {filteredPinned.map((conv) => (
                      <SidebarItem
                        key={conv.id}
                        conversation={conv}
                        isActive={conv.id === activeConversationId}
                        onSelect={() => handleSelect(conv.id)}
                        onDelete={() => deleteConversation(conv.id)}
                        onRename={(title) => renameConversation(conv.id, title)}
                        onPin={() => pinConversation(conv.id)}
                        onUnpin={() => unpinConversation(conv.id)}
                      />
                    ))}
                  </ul>
                </div>
              )}

              {/* Date-grouped or flat search results */}
              {query ? (
                filteredUnpinned.length > 0 && (
                  <div className="mb-3">
                    {filteredPinned.length > 0 && (
                      <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-600">
                        Other results
                      </p>
                    )}
                    <ul className="space-y-0.5">
                      {filteredUnpinned.map((conv) => (
                        <SidebarItem
                          key={conv.id}
                          conversation={conv}
                          isActive={conv.id === activeConversationId}
                          onSelect={() => handleSelect(conv.id)}
                          onDelete={() => deleteConversation(conv.id)}
                          onRename={(title) => renameConversation(conv.id, title)}
                          onPin={() => pinConversation(conv.id)}
                          onUnpin={() => unpinConversation(conv.id)}
                        />
                      ))}
                    </ul>
                  </div>
                )
              ) : (
                groups &&
                Object.entries(groups).map(([label, items]) => (
                  <div key={label} className="mb-3">
                    <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-600">
                      {label}
                    </p>
                    <ul className="space-y-0.5">
                      {items.map((conv) => (
                        <SidebarItem
                          key={conv.id}
                          conversation={conv}
                          isActive={conv.id === activeConversationId}
                          onSelect={() => handleSelect(conv.id)}
                          onDelete={() => deleteConversation(conv.id)}
                          onRename={(title) => renameConversation(conv.id, title)}
                          onPin={() => pinConversation(conv.id)}
                          onUnpin={() => unpinConversation(conv.id)}
                        />
                      ))}
                    </ul>
                  </div>
                ))
              )}
            </>
          )}
        </nav>

        {/* Footer */}
        <div className="border-t border-zinc-200 dark:border-zinc-800 px-3 py-3 space-y-2">
          <ThemeToggle className="w-full justify-center" />
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
              {user?.username?.[0]?.toUpperCase() ?? "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-zinc-800 dark:text-zinc-200 truncate">
                {user?.username ?? "Guest"}
              </p>
              <p className="text-[10px] text-zinc-400 truncate">{user?.email ?? ""}</p>
            </div>
            <button
              onClick={logout}
              title="Sign out"
              aria-label="Sign out"
              className="h-6 w-6 rounded-md flex items-center justify-center text-zinc-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors flex-shrink-0"
            >
              <LogOut size={13} />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
