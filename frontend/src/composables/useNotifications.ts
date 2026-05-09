import { ref, onUnmounted } from "vue";
import type { BrowserNotification } from "@/types";

const API_URL = import.meta.env.VITE_API_URL as string;

/**
 * Composable managing Server-Sent Events connection for browser notifications.
 *
 * Connects to notification_service SSE endpoint and displays native
 * browser notifications via the Web Notification API.
 * Automatically reconnects on connection loss.
 */
export function useNotifications() {
  const isConnected = ref(false);
  const permissionGranted = ref(Notification.permission === "granted");

  let eventSource: EventSource | null = null;

  /**
   * Request browser notification permission and connect to SSE stream.
   */
  async function start(): Promise<void> {
    await _requestPermission();
    _connect();
  }

  /**
   * Close the SSE connection.
   */
  function stop(): void {
    eventSource?.close();
    eventSource = null;
    isConnected.value = false;
  }

  async function _requestPermission(): Promise<void> {
    if (Notification.permission === "default") {
      const result = await Notification.requestPermission();
      permissionGranted.value = result === "granted";
    }
  }

  function _connect(): void {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    /**
     * EventSource does not support custom headers natively.
     * We pass the token as a query parameter — notification_service
     * accepts it as a fallback when Authorization header is absent.
     */
    const url = `${API_URL}/api/notifications/stream/?token=${token}`;
    eventSource = new EventSource(url);

    eventSource.onopen = () => {
      isConnected.value = true;
    };

    eventSource.onmessage = (event: MessageEvent<string>) => {
      try {
        const notification = JSON.parse(event.data) as BrowserNotification;
        _showNotification(notification);
      } catch {
        console.error("Failed to parse SSE notification");
      }
    };

    eventSource.onerror = () => {
      isConnected.value = false;
      // EventSource reconnects automatically
    };
  }

  function _showNotification(notification: BrowserNotification): void {
    if (!permissionGranted.value) return;

    const n = new Notification(notification.title, {
      body: notification.body,
      icon: "/favicon.ico",
      data: notification.data,
    });

    n.onclick = () => {
      window.focus();
      n.close();
    };
  }

  onUnmounted(() => {
    stop();
  });

  return {
    isConnected,
    permissionGranted,
    start,
    stop,
  };
}
