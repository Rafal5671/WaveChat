<script setup lang="ts">
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth.store";
import { useUserStore } from "@/stores/user.store";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const userStore = useUserStore();

const email = route.query.email as string;
const code = ref("");
const username = ref("");
const displayName = ref("");
const error = ref<string | null>(null);
const isLoading = ref(false);

async function handleVerify() {
  error.value = null;
  isLoading.value = true;
  try {
    await authStore.verifyEmail(email, code.value);
    await userStore.createProfile(username.value, displayName.value);
    await router.push({ name: "chat" });
  } catch {
    error.value = "Invalid or expired OTP. Please try again.";
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="w-full max-w-sm bg-white rounded-2xl border border-gray-200 p-8">
      <h1 class="text-xl font-medium text-gray-900 mb-2">Verify your email</h1>
      <p class="text-sm text-gray-500 mb-6">Enter the code sent to {{ email }}</p>

      <form @submit.prevent="handleVerify" class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <label class="text-sm text-gray-500">OTP code</label>
          <input
            v-model="code"
            type="text"
            placeholder="123456"
            maxlength="6"
            required
            class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-600 tracking-widest text-center"
          />
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-sm text-gray-500">Username</label>
          <input
            v-model="username"
            type="text"
            placeholder="john_doe"
            required
            class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-600"
          />
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-sm text-gray-500">Display name</label>
          <input
            v-model="displayName"
            type="text"
            placeholder="John Doe"
            required
            class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-600"
          />
        </div>

        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

        <button
          type="submit"
          :disabled="isLoading"
          class="bg-primary-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-primary-800 disabled:opacity-50 transition-colors"
        >
          {{ isLoading ? "Verifying..." : "Verify & continue" }}
        </button>
      </form>
    </div>
  </div>
</template>
