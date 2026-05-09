<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useUserStore } from "@/stores/user.store";
import { useFileUpload } from "@/composables/useFileUpload";

/**
 * Profile view — displays and allows editing of own profile.
 */
const userStore = useUserStore();
const { upload, isUploading } = useFileUpload();

const isEditing = ref(false);
const isSaving = ref(false);
const error = ref<string | null>(null);
const success = ref(false);

const displayName = ref("");
const bio = ref("");
const username = ref("");

onMounted(async () => {
  await userStore.fetchOwnProfile();
  resetForm();
});

function resetForm() {
  displayName.value = userStore.ownProfile?.display_name ?? "";
  bio.value = userStore.ownProfile?.bio ?? "";
  username.value = userStore.ownProfile?.username ?? "";
}

async function handleSave() {
  error.value = null;
  success.value = false;
  isSaving.value = true;

  try {
    await userStore.updateProfile({
      display_name: displayName.value,
      bio: bio.value,
      username: username.value,
    });
    success.value = true;
    isEditing.value = false;
  } catch {
    error.value = "Failed to update profile. Please try again.";
  } finally {
    isSaving.value = false;
  }
}

function handleCancel() {
  resetForm();
  isEditing.value = false;
  error.value = null;
}

async function handleAvatarChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  const result = await upload(file);
  if (!result) return;

  await userStore.updateProfile({ avatar_url: result.url });
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
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex items-start justify-center pt-16 px-4">
    <div class="w-full max-w-lg bg-white rounded-2xl border border-gray-200 p-8">
      <div class="flex items-center justify-between mb-8">
        <h1 class="text-xl font-medium text-gray-900">Profile</h1>
        <RouterLink to="/chat" class="text-sm text-primary-600 hover:underline">
          Back to chat
        </RouterLink>
      </div>

      <div class="flex flex-col items-center mb-8">
        <label class="relative cursor-pointer group">
          <div
            class="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center text-primary-800 text-xl font-medium overflow-hidden"
          >
            <img
              v-if="userStore.ownProfile?.avatar_url"
              :src="userStore.ownProfile.avatar_url"
              alt="Avatar"
              class="w-full h-full object-cover"
            />
            <span v-else>
              {{
                userStore.ownProfile
                  ? getInitials(userStore.ownProfile.display_name || userStore.ownProfile.username)
                  : "?"
              }}
            </span>
          </div>
          <div
            class="absolute inset-0 rounded-full bg-black/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <span class="text-white text-xs">Change</span>
          </div>
          <input
            type="file"
            accept="image/*"
            class="hidden"
            :disabled="isUploading"
            @change="handleAvatarChange"
          />
        </label>
        <p v-if="isUploading" class="text-xs text-gray-400 mt-2">Uploading...</p>
      </div>

      <div v-if="!isEditing" class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <span class="text-xs text-gray-400">Username</span>
          <span class="text-sm text-gray-900">@{{ userStore.ownProfile?.username }}</span>
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-xs text-gray-400">Display name</span>
          <span class="text-sm text-gray-900">{{ userStore.ownProfile?.display_name || "—" }}</span>
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-xs text-gray-400">Bio</span>
          <span class="text-sm text-gray-900">{{ userStore.ownProfile?.bio || "—" }}</span>
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-xs text-gray-400">Phone number</span>
          <span class="text-sm text-gray-900">{{ userStore.ownProfile?.phone_number }}</span>
        </div>

        <p v-if="success" class="text-sm text-green-500">Profile updated successfully.</p>

        <button
          @click="isEditing = true"
          class="mt-2 bg-primary-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-primary-800 transition-colors"
        >
          Edit profile
        </button>
      </div>

      <form v-else @submit.prevent="handleSave" class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <label class="text-xs text-gray-400">Username</label>
          <input
            v-model="username"
            type="text"
            required
            class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-600"
          />
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-xs text-gray-400">Display name</label>
          <input
            v-model="displayName"
            type="text"
            class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-600"
          />
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-xs text-gray-400">Bio</label>
          <textarea
            v-model="bio"
            rows="3"
            maxlength="500"
            class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-600 resize-none"
          />
        </div>

        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

        <div class="flex gap-2">
          <button
            type="button"
            @click="handleCancel"
            class="flex-1 border border-gray-200 text-gray-600 rounded-lg py-2 text-sm hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="isSaving"
            class="flex-1 bg-primary-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-primary-800 disabled:opacity-50 transition-colors"
          >
            {{ isSaving ? "Saving..." : "Save" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
