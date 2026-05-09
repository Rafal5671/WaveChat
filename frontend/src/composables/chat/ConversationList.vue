<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useChatStore } from "@/stores/chat.store";
import { useAuthStore } from "@/stores/auth.store";
import type { Conversation } from "@/types";

/**
 * Left panel showing list of conversations with search.
 */
const router = useRouter();
const chatStore = useChatStore();
const authStore = useAuthStore();

const search = ref("");

const filtered = computed(() =>
  chatStore.conversations.filter((c) => c.name.toLowerCase().includes(search.value.toLowerCase())),
);

function selectConversation(conversation: Conversation) {
  chatStore.activeConversationId = conversation.id;
  router.push({ name: "conversation", params: { conversationId: conversation.id } });
}

function getConversationName(conversation: Conversation): string {
  if (conversation.type === "group") return conversation.name;
  const other = conversation.participants.find((p) => p.user_id !== authStore.userId);
  return other?.user_id ?? "Unknown";
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function formatTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (diffDays === 1) return "yesterday";
  if (diffDays < 7) return date.toLocaleDateString([], { weekday: "short" });
  return date.toLocaleDateString([], { day: "2-digit", month: "2-digit" });
}
</script>

<template>
  <aside class="w-[300px] flex flex-col border-r border-gray-100 flex-shrink-0">
    <div class="p-4 border-b border-gray-100">
      <h2 class="text-base font-medium text-gray-900 mb-3">Messages</h2>
      <div class="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="w-4 h-4 text-gray-400"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
          />
        </svg>
        <input
          v-model="search"
          type="text"
          placeholder="Search conversations..."
          class="bg-transparent text-sm text-gray-700 placeholder-gray-400 outline-none flex-1"
        />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto">
      <button
        v-for="conversation in filtered"
        :key="conversation.id"
        @click="selectConversation(conversation)"
        class="w-full flex items-center gap-3 px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors text-left"
        :class="{ 'bg-primary-50': chatStore.activeConversationId === conversation.id }"
      >
        <div
          class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-800 text-xs font-medium flex-shrink-0"
        >
          {{ getInitials(getConversationName(conversation)) }}
        </div>

        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-900 truncate">
              {{ getConversationName(conversation) }}
            </span>
            <span class="text-xs text-gray-400 flex-shrink-0 ml-2">
              {{ formatTime(conversation.last_message?.created_at) }}
            </span>
          </div>
          <p class="text-xs text-gray-500 truncate mt-0.5">
            {{
              conversation.last_message?.is_deleted
                ? "Message deleted"
                : (conversation.last_message?.content ?? "")
            }}
          </p>
        </div>
      </button>

      <p v-if="filtered.length === 0" class="text-sm text-gray-400 text-center mt-8">
        No conversations found.
      </p>
    </div>
  </aside>
</template>
