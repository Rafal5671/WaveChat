<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth.store";
import { useUserStore } from "@/stores/user.store";

/**
 * Left sidebar with navigation icons and user avatar.
 */
const router = useRouter();
const authStore = useAuthStore();
const userStore = useUserStore();

async function handleLogout() {
  await authStore.logout();
  await router.push({ name: "login" });
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
  <nav class="flex flex-col items-center w-[72px] bg-[#1a1a2e] py-5 gap-2 flex-shrink-0">
    <div
      class="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center text-white text-sm font-medium mb-4 cursor-pointer"
    >
      {{
        userStore.ownProfile
          ? getInitials(userStore.ownProfile.display_name || userStore.ownProfile.username)
          : "?"
      }}
    </div>

    <RouterLink
      to="/chat"
      class="w-10 h-10 rounded-xl flex items-center justify-center text-gray-400 hover:bg-white/10 hover:text-white transition-colors"
      active-class="bg-primary-600 text-white"
      aria-label="Messages"
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
          d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z"
        />
      </svg>
    </RouterLink>

    <RouterLink
      to="/profile"
      class="w-10 h-10 rounded-xl flex items-center justify-center text-gray-400 hover:bg-white/10 hover:text-white transition-colors"
      active-class="bg-primary-600 text-white"
      aria-label="Profile"
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
          d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"
        />
      </svg>
    </RouterLink>

    <div class="mt-auto">
      <button
        @click="handleLogout"
        class="w-10 h-10 rounded-xl flex items-center justify-center text-gray-400 hover:bg-white/10 hover:text-white transition-colors"
        aria-label="Logout"
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
            d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9"
          />
        </svg>
      </button>
    </div>
  </nav>
</template>
