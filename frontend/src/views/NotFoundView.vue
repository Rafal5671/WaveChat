<script setup lang="ts">
/**
 * 404 Not Found view.
 */
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="text-center">
      <h1 class="text-6xl font-medium text-primary-600 mb-4">404</h1>
      <p class="text-gray-500 mb-6">Page not found.</p>
      <RouterLink to="/chat" class="text-sm text-primary-600 hover:underline">
        Go back to chat
      </RouterLink>
    </div>
  </div>
</template>
