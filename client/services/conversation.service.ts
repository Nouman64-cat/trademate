import axiosInstance from "@/lib/axiosInstance";

export interface ConversationSummary {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface MessageSummary {
  id: number;
  role: string;
  content: string;
  tools_used: string[] | null;
  rating: number | null;
  created_at: string;
}

const ConversationService = {
  fetchConversations: async (): Promise<ConversationSummary[]> => {
    const { data } = await axiosInstance.get<ConversationSummary[]>("/v1/conversations");
    return data;
  },

  fetchMessages: async (conversationId: string): Promise<MessageSummary[]> => {
    const { data } = await axiosInstance.get<MessageSummary[]>(
      `/v1/conversations/${conversationId}/messages`
    );
    return data;
  },
};

export default ConversationService;
