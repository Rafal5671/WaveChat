<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute } from "vue-router";
import { useChatStore } from "@/stores/chat.store";
import { useUserStore } from "@/stores/user.store";
import { useNotifications } from "@/composables/useNotifications";
import ConversationList from "@/components/chat/ConversationList.vue";
import ConversationWindow from "@/components/chat/ConversationWindow.vue";
import SidebarNav from "@/components/chat/SidebarNav.vue";

/**
 * Main chat view — renders sidebar nav, conversation list and active conversation.
 * Fetches initial data and starts SSE notification stream on mount.
 */
const route = useRoute();
const chatStore = useChatStore();
const userStore = useUserStore();
const { start: startNotifications } = useNotifications();

const conversationId = route.params.conversationId as string | undefined;

onMounted(async () => {
  await Promise.all([chatStore.fetchConversations(), userStore.fetchOwnProfile()]);
  await startNotifications();
});
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-white">
    <SidebarNav />
    <ConversationList />
    <ConversationWindow :conversation-id="conversationId ?? null" />
  </div>
</template>
