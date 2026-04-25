import axiosInstance from "@/lib/axiosInstance";
import axios from "axios";

export interface SharedMessage {
  id: number;
  role: string;
  content: string;
  created_at: string;
}

export interface SharedConversation {
  title: string | null;
  messages: SharedMessage[];
}

const ShareService = {
  createShareLink: async (conversationId: string): Promise<string> => {
    const { data } = await axiosInstance.post<{ share_token: string }>(
      `/v1/conversations/${conversationId}/share`
    );
    return data.share_token;
  },

  fetchShared: async (token: string): Promise<SharedConversation> => {
    const base = process.env.NEXT_PUBLIC_SERVER_URL ?? "http://localhost:8000";
    const { data } = await axios.get<SharedConversation>(`${base}/v1/shared/${token}`);
    return data;
  },
};

export default ShareService;
