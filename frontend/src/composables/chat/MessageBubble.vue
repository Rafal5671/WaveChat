<script setup lang="ts">
import type { Message } from "@/types";

/**
 * Single message bubble component.
 * Renders differently based on whether the message belongs to the current user.
 */
const props = defineProps<{
  message: Message;
  isOwn: boolean;
}>();

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}
</script>

<template>
  <div class="flex items-end gap-2" :class="isOwn ? 'flex-row-reverse' : 'flex-row'">
    <div
      v-if="!isOwn"
      class="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center text-primary-800 text-xs font-medium flex-shrink-0"
    >
      ?
    </div>

    <div class="max-w-[62%]">
      <div
        v-if="message.is_deleted"
        class="px-4 py-2 rounded-2xl text-sm italic text-gray-400 border border-gray-200"
        :class="isOwn ? 'rounded-br-sm' : 'rounded-bl-sm'"
      >
        Message deleted
      </div>

      <template v-else>
        <img
          v-if="message.message_type === 'image'"
          :src="message.media_url || message.content"
          alt="Image"
          class="rounded-xl max-w-full max-h-48 object-cover border border-gray-200"
        />

        <div
          v-else
          class="px-4 py-2 rounded-2xl text-sm leading-relaxed"
          :class="
            isOwn
              ? 'bg-primary-600 text-white rounded-br-sm'
              : 'bg-gray-100 text-gray-800 rounded-bl-sm'
          "
        >
          {{ message.content }}
        </div>
      </template>

      <div class="flex items-center gap-1 mt-1" :class="isOwn ? 'justify-end' : 'justify-start'">
        <span class="text-xs text-gray-400">{{ formatTime(message.created_at) }}</span>
        <span
          v-if="isOwn"
          class="text-xs"
          :class="message.status === 'read' ? 'text-primary-600' : 'text-gray-400'"
        >
          {{ message.status === "read" ? "✓✓" : "✓" }}
        </span>
      </div>
    </div>
  </div>
</template>
