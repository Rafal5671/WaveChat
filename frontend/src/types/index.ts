// ── Auth ─────────────────────────────────────────────────────

export interface AuthTokens {
  access: string;
  refresh: string;
  user_id: string;
}

export interface TokenPayload {
  user_id: string;
  phone_number: string;
  is_verified: boolean;
  exp: number;
}

// ── User ─────────────────────────────────────────────────────

export interface Profile {
  id: string;
  username: string;
  display_name: string;
  bio: string;
  avatar_url: string;
  phone_number: string;
  is_online: boolean;
  last_seen: string | null;
  created_at: string;
  updated_at: string;
}

export interface PublicProfile {
  id: string;
  username: string;
  display_name: string;
  avatar_url: string;
  is_online: boolean;
  last_seen: string | null;
}

export interface Contact {
  id: string;
  contact: PublicProfile;
  nickname: string;
  is_blocked: boolean;
  created_at: string;
}

// ── Chat ─────────────────────────────────────────────────────

export type MessageType = "text" | "image" | "video" | "audio" | "file";
export type MessageStatus = "sent" | "delivered" | "read";
export type ConversationType = "direct" | "group";

export interface Message {
  id: string;
  conversation: string;
  sender_id: string;
  content: string;
  message_type: MessageType;
  media_url: string;
  media_metadata: Record<string, unknown>;
  reply_to: string | null;
  status: MessageStatus;
  is_deleted: boolean;
  edited_at: string | null;
  read_at: string | null;
  created_at: string;
}

export interface ConversationParticipant {
  id: string;
  user_id: string;
  role: "member" | "admin";
  joined_at: string;
  last_seen: string | null;
  muted_until: string | null;
}

export interface Conversation {
  id: string;
  type: ConversationType;
  name: string;
  avatar_url: string;
  created_by: string;
  participants: ConversationParticipant[];
  last_message: Message | null;
  created_at: string;
  updated_at: string;
}

// ── WebSocket events ──────────────────────────────────────────

export interface WsMessageEvent {
  type: "message";
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  message_type: MessageType;
  reply_to: string | null;
  created_at: string;
  status: MessageStatus;
}

export interface WsTypingEvent {
  type: "typing";
  user_id: string;
  is_typing: boolean;
}

export interface WsReadReceiptEvent {
  type: "read_receipt";
  message_id: string;
  reader_id: string;
  read_at: string;
}

export interface WsHistoryEvent {
  type: "history";
  messages: Message[];
}

export interface WsErrorEvent {
  type: "error";
  message: string;
}

export type WsEvent =
  | WsMessageEvent
  | WsTypingEvent
  | WsReadReceiptEvent
  | WsHistoryEvent
  | WsErrorEvent;

// ── Media ─────────────────────────────────────────────────────

export interface MediaUploadResponse {
  id: string;
  url: string;
  thumbnail_url: string | null;
  media_type: string;
  mime_type: string;
  size_bytes: number;
  file_name: string;
}

// ── Notifications ─────────────────────────────────────────────

export interface BrowserNotification {
  type: "notification";
  title: string;
  body: string;
  data: {
    type: string;
    conversation_id: string;
    message_id: string;
    sender_id: string;
  };
}

// ── API responses ─────────────────────────────────────────────

export interface ApiError {
  error: string;
}

export interface PaginatedMessages {
  messages: Message[];
  has_more: boolean;
}
