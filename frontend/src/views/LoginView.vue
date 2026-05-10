<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth.store";

const router = useRouter();
const authStore = useAuthStore();

const email = ref("");
const password = ref("");
const error = ref<string | null>(null);
const isLoading = ref(false);

async function handleLogin() {
  error.value = null;
  isLoading.value = true;
  try {
    await authStore.login(email.value, password.value);
    await router.push({ name: "chat" });
  } catch {
    error.value = "Invalid email or password.";
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="w-full max-w-sm bg-white rounded-2xl border border-gray-200 p-8">
      <h1 class="text-xl font-medium text-gray-900 mb-6">Sign in to WaveChat</h1>

      <form @submit.prevent="handleLogin" class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <label class="text-sm text-gray-500">Email</label>
          <input
            v-model="email"
            type="email"
            placeholder="you@example.com"
            required
            class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-600"
          />
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-sm text-gray-500">Password</label>
          <input
            v-model="password"
            type="password"
            placeholder="········"
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
          {{ isLoading ? "Signing in..." : "Sign in" }}
        </button>
      </form>

      <p class="text-sm text-gray-500 text-center mt-4">
        No account?
        <RouterLink to="/register" class="text-primary-600 hover:underline">Register</RouterLink>
      </p>
    </div>
  </div>
</template>
