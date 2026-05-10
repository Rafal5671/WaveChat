<script setup lang="ts">
import { ref, watch } from "vue";
import { useUserStore } from "@/stores/user.store";
import { useChatStore } from "@/stores/chat.store";
import { useRouter } from "vue-router";
import type { PublicProfile } from "@/types";

/**
 * Modal for starting a new direct conversation.
 * Searches users by username and creates a direct conversation on select.
 */
const emit = defineEmits<{
  close: [];
}>();

const userStore = useUserStore();
const chatStore = useChatStore();
const router = useRouter();

const query = ref("");
const results = ref<PublicProfile[]>([]);
const isSearching = ref(false);
const isCreating = ref(false);

let searchTimeout: ReturnType<typeof setTimeout> | null = null;

watch(query, (val) => {
  if (searchTimeout) clearTimeout(searchTimeout);
  if (val.trim().length < 2) {
    results.value = [];
    return;
  }
  searchTimeout = setTimeout(() => search(val.trim()), 400);
});

async function search(q: string) {
  isSearching.value = true;
  try {
    results.value = await userStore.searchProfiles(q);
  } finally {
    isSearching.value = false;
  }
}

async function startConversation(profile: PublicProfile) {
  isCreating.value = true;
  try {
    const conversation = await chatStore.createConversation("direct", [profile.id]);
    emit("close");
    await router.push({ name: "conversation", params: { conversationId: conversation.id } });
  } finally {
    isCreating.value = false;
  }
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}
</script>

<template>
  <div
    class="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
    @click.self="emit('close')"
  >
    <div class="bg-white rounded-2xl border border-gray-200 w-full max-w-md p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-base font-medium text-gray-900">New conversation</h2>
        <button
          @click="emit('close')"
          class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 transition-colors"
          aria-label="Close"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div
        class="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 mb-4"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="w-4 h-4 text-gray-400 flex-shrink-0"
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
          v-model="query"
          type="text"
          placeholder="Search by username..."
          autofocus
          class="bg-transparent text-sm text-gray-700 placeholder-gray-400 outline-none flex-1"
        />
        <span v-if="isSearching" class="text-xs text-gray-400">Searching...</span>
      </div>

      <div class="flex flex-col gap-1 max-h-64 overflow-y-auto">
        <button
          v-for="profile in results"
          :key="profile.id"
          @click="startConversation(profile)"
          :disabled="isCreating"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors text-left disabled:opacity-50"
        >
          <div
            class="w-9 h-9 rounded-full bg-primary-100 flex items-center justify-center text-primary-800 text-xs font-medium flex-shrink-0 overflow-hidden"
          >
            <img
              v-if="profile.avatar_url"
              :src="profile.avatar_url"
              :alt="profile.username"
              class="w-full h-full object-cover"
            />
            <span v-else>{{ getInitials(profile.display_name || profile.username) }}</span>
          </div>
          <div>
            <p class="text-sm font-medium text-gray-900">
              {{ profile.display_name || profile.username }}
            </p>
            <p class="text-xs text-gray-400">@{{ profile.username }}</p>
          </div>
          <div
            v-if="profile.is_online"
            class="ml-auto w-2 h-2 rounded-full bg-green-400 flex-shrink-0"
          />
        </button>

        <p
          v-if="query.length >= 2 && !isSearching && results.length === 0"
          class="text-sm text-gray-400 text-center py-4"
        >
          No users found.
        </p>

        <p v-if="query.length < 2" class="text-sm text-gray-400 text-center py-4">
          Type at least 2 characters to search.
        </p>
      </div>
    </div>
  </div>
</template>
