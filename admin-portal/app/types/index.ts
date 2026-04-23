/**
 * Type Definitions for Admin Portal
 */

// ==================== User Management ====================

export interface User {
  id: number;
  email: string;
  full_name: string;
  trade_role: 'importer' | 'exporter' | 'freight_forwarder' | 'customs_broker' | 'other';
  target_region: 'PK' | 'US' | 'global';
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface UserFilters {
  search?: string;
  trade_role?: string;
  is_verified?: boolean;
  is_active?: boolean;
  page?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

// ==================== Chatbot Configuration ====================

export interface ChatbotConfig {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  config: ChatbotSettings;
}

export interface ChatbotSettings {
  // LLM Settings
  llm_model: string;
  temperature: number;
  max_tokens: number;
  top_p: number;

  // Agent Settings
  available_tools: string[];
  router_enabled: boolean;
  max_tool_calls: number;

  // Rate Limiting
  max_messages_per_hour: number;
  max_conversations_per_day: number;

  // Features
  document_search_enabled: boolean;
  route_evaluation_enabled: boolean;
  hs_code_search_enabled: boolean;

  // Personalization
  recommendation_enabled: boolean;
  interaction_tracking_enabled: boolean;
}

// ==================== Analytics ====================

export interface AnalyticsOverview {
  total_users: number;
  active_users_today: number;
  total_conversations: number;
  total_messages: number;
  avg_messages_per_conversation: number;
  popular_tools: { name: string; count: number }[];
  popular_hs_codes: { code: string; searches: number }[];
}

export interface ConversationMetrics {
  date: string;
  conversations: number;
  messages: number;
  avg_rating: number;
}

// ==================== API Response Types ====================

export interface APIError {
  detail: string;
  code?: string;
}

export interface SuccessResponse {
  message: string;
  data?: any;
}

// ==================== Navigation ====================

export interface NavItem {
  title: string;
  href: string;
  icon: any; // Lucide icon component
  badge?: number;
  children?: NavItem[];
}

export interface BreadcrumbItem {
  title: string;
  href?: string;
}
