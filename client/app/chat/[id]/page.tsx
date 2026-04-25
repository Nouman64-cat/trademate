"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useChatStore } from "@/stores/chatStore";
import { useChat } from "@/hooks/useChat";
import { MessageList } from "@/components/chat/MessageList";
import { ChatInput } from "@/components/chat/ChatInput";
import { ChatHeader } from "@/components/layout/ChatHeader";
import { WelcomeScreen } from "@/components/chat/WelcomeScreen";
import ConversationService from "@/services/conversation.service";
import type { Message, Role } from "@/types";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ConversationPage({ params }: PageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { conversations, setActiveConversation, setMessagesForConversation } = useChatStore();
  const { sendMessage, isStreaming } = useChat();
  const [loadingMessages, setLoadingMessages] = useState(false);

  const conversation = conversations.find((c) => c.id === id);

  // Sync active conversation ID with URL param
  useEffect(() => {
    setActiveConversation(id);
  }, [id, setActiveConversation]);

  // If conversation doesn't exist (e.g. after deletion), go to /chat
  useEffect(() => {
    if (conversations.length > 0 && !conversation) {
      router.replace("/chat");
    }
  }, [conversation, conversations.length, router]);

  // Lazy-load messages for server-synced conversations that haven't been fetched yet
  useEffect(() => {
    if (!conversation || conversation.messagesLoaded !== false) return;

    setLoadingMessages(true);
    ConversationService.fetchMessages(id)
      .then((msgs) => {
        const messages: Message[] = msgs.map((m) => ({
          id: String(m.id),
          role: m.role as Role,
          content: m.content,
          createdAt: new Date(m.created_at),
          dbId: m.id,
          rating: m.rating ?? undefined,
        }));
        setMessagesForConversation(id, messages);
      })
      .catch(() => {
        // Mark as loaded even on error to prevent retry loop
        setMessagesForConversation(id, []);
      })
      .finally(() => setLoadingMessages(false));
  }, [id, conversation?.messagesLoaded]);

  const handleSend = (message: string) => sendMessage(id, message);

  if (!conversation) return null;

  return (
    <div className="flex flex-col h-full bg-white dark:bg-zinc-900">
      <ChatHeader />

      {loadingMessages ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="h-5 w-5 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
        </div>
      ) : conversation.messages.length === 0 ? (
        <WelcomeScreen onPromptSelect={handleSend} />
      ) : (
        <MessageList messages={conversation.messages} isStreaming={isStreaming} />
      )}

      <ChatInput onSend={handleSend} isStreaming={isStreaming} />
    </div>
  );
}
