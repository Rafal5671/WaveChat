import { defineStore } from "pinia";
import { ref } from "vue";
import { chatService } from "@/services/chat.service";
import type { Conversation, Message } from "@/types";

/**
 * Manages conversation list and per-conversation message state.
 * Messages are stored in a Map keyed by conversation ID.
 */
export const useChatStore = defineStore("chat", () => {
  const conversations = ref<Conversation[]>([]);
  const messages = ref<Map<string, Message[]>>(new Map());
  const activeConversationId = ref<string | null>(null);
  const typingUsers = ref<Map<string, Set<string>>>(new Map());

  /**
   * Fetch and store all conversations for the current user.
   */
  async function fetchConversations(): Promise<void> {
    conversations.value = await chatService.getConversations();
  }

  /**
   * Fetch messages for a conversation and store them.
   */
  async function fetchMessages(conversationId: string): Promise<void> {
    const fetched = await chatService.getMessages(conversationId);
    messages.value.set(conversationId, fetched);
  }

  /**
   * Load older messages for a conversation (pagination).
   */
  async function loadMoreMessages(conversationId: string): Promise<void> {
    const existing = messages.value.get(conversationId) ?? [];
    const oldest = existing[0]?.created_at;
    const older = await chatService.getMessages(conversationId, oldest);
    messages.value.set(conversationId, [...older, ...existing]);
  }

  /**
   * Append a new message to a conversation — called on WebSocket message event.
   */
  function appendMessage(conversationId: string, message: Message): void {
    const existing = messages.value.get(conversationId) ?? [];
    if (existing.some((m) => m.id === message.id)) return;
    messages.value.set(conversationId, [...existing, message]);
    _bumpConversation(conversationId, message);
  }

  /**
   * Update message status — called on read receipt WebSocket event.
   */
  function updateMessageStatus(
    conversationId: string,
    messageId: string,
    status: Message["status"],
    readAt: string,
  ): void {
    const msgs = messages.value.get(conversationId);
    if (!msgs) return;
    const msg = msgs.find((m) => m.id === messageId);
    if (msg) {
      msg.status = status;
      msg.read_at = readAt;
    }
  }

  /**
   * Set or clear typing indicator for a user in a conversation.
   */
  function setTyping(conversationId: string, userId: string, isTyping: boolean): void {
    if (!typingUsers.value.has(conversationId)) {
      typingUsers.value.set(conversationId, new Set());
    }
    const users = typingUsers.value.get(conversationId)!;
    if (isTyping) {
      users.add(userId);
    } else {
      users.delete(userId);
    }
  }

  /**
   * Return messages for a given conversation.
   */
  function getMessages(conversationId: string): Message[] {
    return messages.value.get(conversationId) ?? [];
  }

  /**
   * Return typing users for a given conversation.
   */
  function getTypingUsers(conversationId: string): string[] {
    return Array.from(typingUsers.value.get(conversationId) ?? []);
  }

  /**
   * Create a new conversation and prepend it to the list.
   */
  async function createConversation(
    type: "direct" | "group",
    participantIds: string[],
    name?: string,
  ): Promise<Conversation> {
    const conversation = await chatService.createConversation(type, participantIds, name);
    conversations.value.unshift(conversation);
    return conversation;
  }

  /**
   * Move a conversation to the top of the list and update its last message.
   */
  function _bumpConversation(conversationId: string, message: Message): void {
    const index = conversations.value.findIndex((c) => c.id === conversationId);
    if (index === -1) return;

    const existing = conversations.value[index];
    if (!existing) return;

    const updated: Conversation = {
      id: existing.id,
      type: existing.type,
      name: existing.name,
      avatar_url: existing.avatar_url,
      created_by: existing.created_by,
      participants: existing.participants,
      last_message: message,
      created_at: existing.created_at,
      updated_at: existing.updated_at,
    };
    conversations.value.splice(index, 1);
    conversations.value.unshift(updated);
  }

  return {
    conversations,
    messages,
    activeConversationId,
    typingUsers,
    fetchConversations,
    fetchMessages,
    loadMoreMessages,
    appendMessage,
    updateMessageStatus,
    setTyping,
    getMessages,
    getTypingUsers,
    createConversation,
  };
});
