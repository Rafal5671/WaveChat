<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { useChatStore } from "@/stores/chat.store";
import { useAuthStore } from "@/stores/auth.store";
import { useUserStore } from "@/stores/user.store";
import { useWebSocket } from "@/composables/useWebSocket";
import { useFileUpload } from "@/composables/useFileUpload";
import MessageBubble from "@/components/chat/MessageBubble.vue";
import type { Message, PublicProfile } from "@/types";

/**
 * Main chat window showing messages and input for the active conversation.
 * Resolves the other participant's profile and sender profiles from user_service.
 */
const props = defineProps<{
  conversationId: string | null;
}>();

const chatStore = useChatStore();
const authStore = useAuthStore();
const userStore = useUserStore();
const { upload, isUploading } = useFileUpload();

const messageText = ref("");
const messagesEndRef = ref<HTMLDivElement | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);
const otherProfile = ref<PublicProfile | null>(null);
const senderProfiles = ref<Map<string, PublicProfile>>(new Map());

let ws: ReturnType<typeof useWebSocket> | null = null;

// Watch for conversation ID change — connect WebSocket and fetch messages
watch(
  () => props.conversationId,
  async (id) => {
    if (!id) return;

    ws?.disconnect();
    ws = useWebSocket(id);
    ws.connect();

    await chatStore.fetchMessages(id);
    scrollToBottom();
  },
  { immediate: true },
);

// Watch for conversation data — resolve other participant's profile
watch(
  () => {
    if (!props.conversationId) return null;
    return chatStore.conversations.find((c) => c.id === props.conversationId) ?? null;
  },
  async (conversation) => {
    if (!conversation || conversation.type !== "direct") return;

    const currentUserId = authStore.userId;
    const other = conversation.participants.find((p) =>
      currentUserId ? p.user_id !== currentUserId : p.user_id !== conversation.created_by,
    );

    if (!other) return;

    try {
      otherProfile.value = await userStore.getPublicProfile(other.user_id);
    } catch {
      otherProfile.value = null;
    }
  },
  { immediate: true, deep: true },
);

// Watch for messages — resolve sender profiles and scroll to bottom
watch(
  () => chatStore.getMessages(props.conversationId ?? ""),
  async (messages) => {
    await resolveSenderProfiles(messages);
    nextTick(scrollToBottom);
  },
  { deep: true },
);

async function resolveSenderProfiles(messages: Message[]) {
  const ids = new Set(
    messages.filter((m) => m.sender_id !== authStore.userId).map((m) => m.sender_id),
  );

  await Promise.all(
    Array.from(ids).map(async (id) => {
      if (senderProfiles.value.has(id)) return;
      try {
        const profile = await userStore.getPublicProfile(id);
        senderProfiles.value.set(id, profile);
      } catch {
        // fallback — avatar will show '?'
      }
    }),
  );
}

function scrollToBottom() {
  messagesEndRef.value?.scrollIntoView({ behavior: "smooth" });
}

function handleSend() {
  const content = messageText.value.trim();
  if (!content || !ws) return;
  ws.sendMessage(content);
  messageText.value = "";
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    handleSend();
  }
}

let typingTimeout: ReturnType<typeof setTimeout> | null = null;

function handleTyping() {
  if (!ws) return;
  ws.sendTyping(true);
  if (typingTimeout) clearTimeout(typingTimeout);
  typingTimeout = setTimeout(() => ws?.sendTyping(false), 2000);
}

async function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file || !ws) return;

  const result = await upload(file);
  if (!result) return;

  ws.sendMediaMessage(result.url, result.media_type as "image" | "video" | "audio" | "file");
  input.value = "";
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

const typingUsers = () =>
  props.conversationId ? chatStore.getTypingUsers(props.conversationId) : [];
</script>

<template>
  <div class="flex-1 flex flex-col min-w-0">
    <template v-if="conversationId">
      <div class="flex items-center gap-3 px-4 py-3 border-b border-gray-100">
        <div
          class="w-9 h-9 rounded-full bg-primary-100 flex items-center justify-center text-primary-800 text-xs font-medium overflow-hidden flex-shrink-0"
        >
          <img
            v-if="otherProfile?.avatar_url"
            :src="otherProfile.avatar_url"
            alt="avatar"
            class="w-full h-full object-cover"
          />
          <span v-else>
            {{
              otherProfile ? getInitials(otherProfile.display_name || otherProfile.username) : "?"
            }}
          </span>
        </div>

        <div>
          <p class="text-sm font-medium text-gray-900">
            {{ otherProfile?.display_name || otherProfile?.username || "Conversation" }}
          </p>
          <p v-if="typingUsers().length > 0" class="text-xs text-primary-600">typing...</p>
          <p v-else-if="otherProfile?.is_online" class="text-xs text-green-500">online</p>
          <p v-else class="text-xs text-gray-400">offline</p>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3">
        <MessageBubble
          v-for="message in chatStore.getMessages(conversationId)"
          :key="message.id"
          :message="message"
          :is-own="message.sender_id === authStore.userId"
          :sender-profile="senderProfiles.get(message.sender_id) ?? null"
        />
        <div ref="messagesEndRef" />
      </div>

      <div class="px-4 py-3 border-t border-gray-100 flex items-center gap-2">
        <button
          @click="fileInputRef?.click()"
          class="w-9 h-9 rounded-xl flex items-center justify-center text-gray-400 hover:bg-gray-100 transition-colors"
          aria-label="Attach file"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-5 h-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="m18.375 12.739-7.693 7.693a4.5 4.5 0 0 1-6.364-6.364l10.94-10.94A3 3 0 1 1 19.5 7.372L8.552 18.32m.009-.01-.01.01m5.699-9.941-7.81 7.81a1.5 1.5 0 0 0 2.112 2.13"
            />
          </svg>
        </button>

        <input
          ref="fileInputRef"
          type="file"
          class="hidden"
          accept="image/*,video/*,audio/*,.pdf,.zip,.txt,.doc,.docx"
          @change="handleFileSelect"
        />

        <textarea
          v-model="messageText"
          @keydown="handleKeydown"
          @input="handleTyping"
          placeholder="Write a message..."
          rows="1"
          class="flex-1 bg-gray-50 border border-gray-200 rounded-2xl px-4 py-2 text-sm text-gray-700 placeholder-gray-400 outline-none resize-none focus:border-primary-400 transition-colors"
        />

        <button
          @click="handleSend"
          :disabled="!messageText.trim() || isUploading"
          class="w-9 h-9 rounded-full bg-primary-600 flex items-center justify-center text-white hover:bg-primary-800 disabled:opacity-40 transition-colors flex-shrink-0"
          aria-label="Send message"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5"
            />
          </svg>
        </button>
      </div>
    </template>

    <div v-else class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div
          class="w-16 h-16 rounded-full bg-primary-50 flex items-center justify-center mx-auto mb-4"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-8 h-8 text-primary-600"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z"
            />
          </svg>
        </div>
        <p class="text-sm text-gray-500">Select a conversation to start chatting</p>
      </div>
    </div>
  </div>
</template>
