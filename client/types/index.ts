import type { RouteEvaluationResponse } from "@/types/routes";

export type Role = "user" | "assistant" | "system";

export interface MessageWidget {
  type: "route_evaluation";
  data: RouteEvaluationResponse;
}

export interface Message {
  id: string;
  role: Role;
  content: string;
  createdAt: Date;
  widgets?: MessageWidget[];
  // DB primary key, set once the backend has persisted the message. Rating
  // submission requires this — the star UI stays disabled until it arrives.
  dbId?: number;
  // 1–5 star rating the user has submitted for an assistant message.
  rating?: number | null;
}

export interface Conversation {
  id: string;
  title: string;
  titleLoading?: boolean;
  messages: Message[];
  /**
   * false = loaded from server list but messages not yet fetched.
   * undefined or true = messages are already in store (locally created or already fetched).
   */
  messagesLoaded?: boolean;
  /** Set when the conversation is pinned; undefined means not pinned. */
  pinnedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface Model {
  id: string;
  name: string;
  description: string;
}

export type SendMessagePayload = {
  conversationId: string;
  content: string;
};
