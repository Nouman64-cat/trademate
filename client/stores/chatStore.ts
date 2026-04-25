"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Conversation, Message, MessageWidget } from "@/types";
import type { ConversationSummary } from "@/services/conversation.service";
import { generateId, deriveTitleFromMessage } from "@/lib/utils";

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  isStreaming: boolean;
  selectedModelId: string;

  // Actions
  createConversation: () => string;
  deleteConversation: (id: string) => void;
  setActiveConversation: (id: string | null) => void;
  addMessage: (conversationId: string, message: Omit<Message, "id" | "createdAt">) => string;
  updateLastAssistantMessage: (conversationId: string, content: string) => void;
  attachWidgetToLastMessage: (conversationId: string, widget: MessageWidget) => void;
  setLastAssistantMessageDbId: (conversationId: string, dbId: number) => void;
  setMessageRating: (conversationId: string, dbId: number, rating: number) => void;
  setStreaming: (value: boolean) => void;
  setSelectedModel: (modelId: string) => void;
  getActiveConversation: () => Conversation | undefined;
  renameConversation: (id: string, title: string) => void;
  setConversationTitle: (id: string, title: string) => void;
  mergeServerConversations: (serverConvs: ConversationSummary[]) => void;
  setMessagesForConversation: (id: string, messages: Message[]) => void;
  pinConversation: (id: string) => void;
  unpinConversation: (id: string) => void;
  clearAll: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      conversations: [],
      activeConversationId: null,
      isStreaming: false,
      selectedModelId: "trademate-pro",

      createConversation: () => {
        const id = generateId();
        const now = new Date();
        const conversation: Conversation = {
          id,
          title: "New conversation",
          titleLoading: false,
          messages: [],
          messagesLoaded: true,
          createdAt: now,
          updatedAt: now,
        };
        set((state) => ({
          conversations: [conversation, ...state.conversations],
          activeConversationId: id,
        }));
        return id;
      },

      deleteConversation: (id) => {
        set((state) => {
          const remaining = state.conversations.filter((c) => c.id !== id);
          const nextActive =
            state.activeConversationId === id
              ? (remaining[0]?.id ?? null)
              : state.activeConversationId;
          return { conversations: remaining, activeConversationId: nextActive };
        });
      },

      setActiveConversation: (id) => {
        set({ activeConversationId: id });
      },

      addMessage: (conversationId, message) => {
        const id = generateId();
        const newMessage: Message = {
          ...message,
          id,
          createdAt: new Date(),
        };

        set((state) => ({
          conversations: state.conversations.map((conv) => {
            if (conv.id !== conversationId) return conv;

            const isFirstUserMessage =
              message.role === "user" &&
              conv.messages.filter((m) => m.role === "user").length === 0;

            return {
              ...conv,
              // Mark title as loading on first message — server will send the real title
              titleLoading: isFirstUserMessage ? true : conv.titleLoading,
              messages: [...conv.messages, newMessage],
              updatedAt: new Date(),
            };
          }),
        }));

        return id;
      },

      updateLastAssistantMessage: (conversationId, content) => {
        set((state) => ({
          conversations: state.conversations.map((conv) => {
            if (conv.id !== conversationId) return conv;
            const messages = [...conv.messages];
            const lastIdx = messages.length - 1;
            if (lastIdx >= 0 && messages[lastIdx].role === "assistant") {
              messages[lastIdx] = { ...messages[lastIdx], content };
            }
            return { ...conv, messages, updatedAt: new Date() };
          }),
        }));
      },

      attachWidgetToLastMessage: (conversationId, widget) => {
        set((state) => ({
          conversations: state.conversations.map((conv) => {
            if (conv.id !== conversationId) return conv;
            const messages = [...conv.messages];
            const lastIdx = messages.length - 1;
            if (lastIdx >= 0 && messages[lastIdx].role === "assistant") {
              const existing = messages[lastIdx].widgets ?? [];
              messages[lastIdx] = { ...messages[lastIdx], widgets: [...existing, widget] };
            }
            return { ...conv, messages };
          }),
        }));
      },

      setLastAssistantMessageDbId: (conversationId, dbId) => {
        set((state) => ({
          conversations: state.conversations.map((conv) => {
            if (conv.id !== conversationId) return conv;
            const messages = [...conv.messages];
            const lastIdx = messages.length - 1;
            if (lastIdx >= 0 && messages[lastIdx].role === "assistant") {
              messages[lastIdx] = { ...messages[lastIdx], dbId };
            }
            return { ...conv, messages };
          }),
        }));
      },

      setMessageRating: (conversationId, dbId, rating) => {
        set((state) => ({
          conversations: state.conversations.map((conv) => {
            if (conv.id !== conversationId) return conv;
            return {
              ...conv,
              messages: conv.messages.map((m) =>
                m.dbId === dbId ? { ...m, rating } : m
              ),
            };
          }),
        }));
      },

      setStreaming: (value) => set({ isStreaming: value }),

      setSelectedModel: (modelId) => set({ selectedModelId: modelId }),

      getActiveConversation: () => {
        const { conversations, activeConversationId } = get();
        return conversations.find((c) => c.id === activeConversationId);
      },

      renameConversation: (id, title) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === id ? { ...c, title } : c
          ),
        }));
      },

      setConversationTitle: (id, title) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === id ? { ...c, title, titleLoading: false } : c
          ),
        }));
      },

      mergeServerConversations: (serverConvs) => {
        set((state) => {
          const byId = new Map(state.conversations.map((c) => [c.id, c]));
          const serverIds = new Set(serverConvs.map((s) => s.id));

          const merged: Conversation[] = serverConvs.map((sc) => {
            const existing = byId.get(sc.id);
            // Keep existing entry if messages are already loaded (!== false covers undefined = old data)
            if (existing && existing.messagesLoaded !== false) {
              return { ...existing, title: sc.title ?? existing.title };
            }
            return {
              id: sc.id,
              title: sc.title ?? "Untitled",
              titleLoading: false,
              messages: existing?.messages ?? [],
              messagesLoaded: existing?.messagesLoaded ?? false,
              createdAt: new Date(sc.created_at),
              updatedAt: new Date(sc.updated_at),
            };
          });

          // Preserve locally-created conversations not yet on the server
          const localOnly = state.conversations.filter((c) => !serverIds.has(c.id));
          return { conversations: [...merged, ...localOnly] };
        });
      },

      setMessagesForConversation: (id, messages) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === id ? { ...c, messages, messagesLoaded: true } : c
          ),
        }));
      },

      pinConversation: (id) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === id ? { ...c, pinnedAt: new Date() } : c
          ),
        }));
      },

      unpinConversation: (id) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === id ? { ...c, pinnedAt: undefined } : c
          ),
        }));
      },

      clearAll: () => {
        set({ conversations: [], activeConversationId: null, isStreaming: false });
      },
    }),
    {
      name: "trademate-chat",
      // Revive Date objects from JSON
      onRehydrateStorage: () => (state) => {
        if (!state) return;
        state.conversations = state.conversations.map((conv) => ({
          ...conv,
          createdAt: new Date(conv.createdAt),
          updatedAt: new Date(conv.updatedAt),
          pinnedAt: conv.pinnedAt ? new Date(conv.pinnedAt) : undefined,
          messages: conv.messages.map((m) => ({
            ...m,
            createdAt: new Date(m.createdAt),
          })),
        }));
      },
    }
  )
);
