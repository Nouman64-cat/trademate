"use client";

import { useCallback } from "react";
import { useChatStore } from "@/stores/chatStore";
import { streamChat } from "@/services/chat.service";

/**
 * Encapsulates sending a message and handling the streaming response
 * from POST /v1/chat.
 */
export function useChat() {
  const {
    conversations,
    addMessage,
    updateLastAssistantMessage,
    setStreaming,
    isStreaming,
  } = useChatStore();

  const sendMessage = useCallback(
    async (conversationId: string, content: string) => {
      if (!content.trim() || isStreaming) return;

      // Snapshot history *before* adding the new user message
      const currentConversation = conversations.find((c: { id: string }) => c.id === conversationId);
      const history = currentConversation?.messages ?? [];

      addMessage(conversationId, { role: "user", content });

      // Placeholder that will be filled in token by token
      addMessage(conversationId, { role: "assistant", content: "" });
      setStreaming(true);

      try {
        await streamChat(
          content,
          conversationId,
          history,
          (accumulated) => updateLastAssistantMessage(conversationId, accumulated),
        );
      } catch (err) {
        const detail = err instanceof Error ? err.message : "Something went wrong.";
        updateLastAssistantMessage(conversationId, `\u26a0\ufe0f ${detail}`);
      } finally {
        setStreaming(false);
      }
    },
    [conversations, addMessage, updateLastAssistantMessage, setStreaming, isStreaming]
  );

  return { sendMessage, isStreaming };
}
