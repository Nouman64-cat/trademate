"use client";

import { useRouter } from "next/navigation";
import { useChatStore } from "@/stores/chatStore";
import { useChat } from "@/hooks/useChat";
import { WelcomeScreen } from "@/components/chat/WelcomeScreen";
import { ChatInput } from "@/components/chat/ChatInput";
import { ChatHeader } from "@/components/layout/ChatHeader";

export default function NewChatPage() {
  const router = useRouter();
  const { createConversation } = useChatStore();
  const { sendMessage, isStreaming } = useChat();

  const handleSend = async (message: string) => {
    const id = createConversation();
    // Redirect immediately so the UI switches to the conversation view.
    // The sendMessage call updates the global store, which the new page will reflect.
    router.push(`/chat/${id}`);
    sendMessage(id, message);
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-zinc-900">
      <ChatHeader />
      <WelcomeScreen onPromptSelect={handleSend} />
      <ChatInput onSend={handleSend} isStreaming={isStreaming} />
    </div>
  );
}
