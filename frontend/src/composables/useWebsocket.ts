import { ref, onUnmounted } from "vue";
import { useChatStore } from "@/stores/chat.store";
import type { Message, WsEvent, WsMessageEvent } from "@/types";

const WS_URL = import.meta.env.VITE_WS_URL as string;

/**
 * Composable managing a WebSocket connection to a single conversation.
 *
 * Handles connection lifecycle, reconnection on unexpected close,
 * and dispatches incoming events to the chat store.
 */
export function useWebSocket(conversationId: string) {
  const chatStore = useChatStore();

  const isConnected = ref(false);
  const isReconnecting = ref(false);

  let socket: WebSocket | null = null;
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  let reconnectAttempts = 0;
  const MAX_RECONNECT_ATTEMPTS = 5;

  /**
   * Open WebSocket connection with JWT token in query string.
   */
  function connect(): void {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    const url = `${WS_URL}/ws/chat/${conversationId}/?token=${token}`;
    socket = new WebSocket(url);

    socket.onopen = () => {
      isConnected.value = true;
      isReconnecting.value = false;
      reconnectAttempts = 0;
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const data = JSON.parse(event.data) as WsEvent;
        _handleEvent(data);
      } catch {
        console.error("Failed to parse WebSocket message");
      }
    };

    socket.onclose = (event: CloseEvent) => {
      isConnected.value = false;

      // Do not reconnect on auth errors
      if (event.code === 4001 || event.code === 4003 || event.code === 4004) {
        return;
      }

      _scheduleReconnect();
    };

    socket.onerror = () => {
      isConnected.value = false;
    };
  }

  /**
   * Send a text message through the WebSocket.
   */
  function sendMessage(content: string, replyTo?: string): void {
    _send({
      type: "message",
      content,
      message_type: "text",
      reply_to: replyTo ?? null,
    });
  }

  /**
   * Send a media message through the WebSocket.
   */
  function sendMediaMessage(
    mediaUrl: string,
    messageType: Message["message_type"],
    replyTo?: string,
  ): void {
    _send({
      type: "message",
      content: mediaUrl,
      message_type: messageType,
      reply_to: replyTo ?? null,
    });
  }

  /**
   * Send a typing indicator event.
   */
  function sendTyping(isTyping: boolean): void {
    _send({ type: "typing", is_typing: isTyping });
  }

  /**
   * Send a read receipt for a message.
   */
  function sendReadReceipt(messageId: string): void {
    _send({ type: "read", message_id: messageId });
  }

  /**
   * Close the WebSocket connection cleanly.
   */
  function disconnect(): void {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    socket?.close();
    socket = null;
    isConnected.value = false;
  }

  function _send(payload: Record<string, unknown>): void {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload));
    }
  }

  function _handleEvent(event: WsEvent): void {
    switch (event.type) {
      case "history":
        event.messages.forEach((msg) => {
          chatStore.appendMessage(conversationId, msg);
        });
        break;

      case "message":
        chatStore.appendMessage(conversationId, _wsMessageToMessage(event));
        break;

      case "typing":
        chatStore.setTyping(conversationId, event.user_id, event.is_typing);
        break;

      case "read_receipt":
        chatStore.updateMessageStatus(conversationId, event.message_id, "read", event.read_at);
        break;

      case "error":
        console.error("WebSocket error from server:", event.message);
        break;
    }
  }

  function _wsMessageToMessage(event: WsMessageEvent): Message {
    return {
      id: event.id,
      conversation: event.conversation_id,
      sender_id: event.sender_id,
      content: event.content,
      message_type: event.message_type,
      media_url: "",
      media_metadata: {},
      reply_to: event.reply_to,
      status: event.status,
      is_deleted: false,
      edited_at: null,
      read_at: null,
      created_at: event.created_at,
    };
  }

  function _scheduleReconnect(): void {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.error("Max reconnect attempts reached.");
      return;
    }

    isReconnecting.value = true;
    reconnectAttempts++;
    const delay = Math.min(1000 * 2 ** reconnectAttempts, 30000);

    reconnectTimeout = setTimeout(() => {
      connect();
    }, delay);
  }

  onUnmounted(() => {
    disconnect();
  });

  return {
    isConnected,
    isReconnecting,
    connect,
    disconnect,
    sendMessage,
    sendMediaMessage,
    sendTyping,
    sendReadReceipt,
  };
}
