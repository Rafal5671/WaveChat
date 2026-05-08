import api from "./api";
import type { Conversation, Message } from "@/types";

/**
 * Handles REST communication with chat_service via API Gateway.
 * WebSocket communication is handled separately in useChat composable.
 */
export const chatService = {
  /**
   * Return all conversations for the current user.
   */
  async getConversations(): Promise<Conversation[]> {
    const { data } = await api.get("/api/chat/conversations/");
    return data;
  },

  /**
   * Return a single conversation by ID.
   */
  async getConversation(conversationId: string): Promise<Conversation> {
    const { data } = await api.get(`/api/chat/conversations/${conversationId}/`);
    return data;
  },

  /**
   * Create a new direct or group conversation.
   */
  async createConversation(
    type: "direct" | "group",
    participantIds: string[],
    name?: string,
  ): Promise<Conversation> {
    const { data } = await api.post("/api/chat/conversations/", {
      type,
      participant_ids: participantIds,
      name,
    });
    return data;
  },

  /**
   * Return paginated messages for a conversation.
   */
  async getMessages(conversationId: string, before?: string, limit = 50): Promise<Message[]> {
    const { data } = await api.get(`/api/chat/conversations/${conversationId}/messages/`, {
      params: { before, limit },
    });
    return data;
  },

  /**
   * Edit a message by ID.
   */
  async editMessage(messageId: string, content: string): Promise<Message> {
    const { data } = await api.patch(`/api/chat/messages/${messageId}/`, { content });
    return data;
  },

  /**
   * Soft-delete a message by ID.
   */
  async deleteMessage(messageId: string): Promise<void> {
    await api.delete(`/api/chat/messages/${messageId}/`);
  },
};
