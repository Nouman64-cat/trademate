"use client";

import { useEffect } from "react";
import { useChatStore } from "@/stores/chatStore";
import ConversationService from "@/services/conversation.service";

export function ConversationLoader() {
  const { mergeServerConversations } = useChatStore();

  useEffect(() => {
    ConversationService.fetchConversations()
      .then(mergeServerConversations)
      .catch(() => {});
  }, []);

  return null;
}
