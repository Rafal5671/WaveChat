import { defineStore } from "pinia";
import { ref } from "vue";
import { userService } from "@/services/user.service";
import type { Contact, Profile, PublicProfile } from "@/types";

/**
 * Manages user profile state and contact list.
 * Caches public profiles to avoid redundant API calls.
 */
export const useUserStore = defineStore("user", () => {
  const ownProfile = ref<Profile | null>(null);
  const contacts = ref<Contact[]>([]);
  const profileCache = ref<Map<string, PublicProfile>>(new Map());

  /**
   * Fetch and store own profile from user_service.
   */
  async function fetchOwnProfile(): Promise<void> {
    ownProfile.value = await userService.getOwnProfile();
  }

  /**
   * Create a new profile after registration.
   */
  async function createProfile(username: string, displayName: string): Promise<void> {
    ownProfile.value = await userService.createProfile(username, displayName);
  }

  /**
   * Update own profile fields.
   */
  async function updateProfile(
    payload: Partial<Pick<Profile, "username" | "display_name" | "bio" | "avatar_url">>,
  ): Promise<void> {
    ownProfile.value = await userService.updateProfile(payload);
  }

  /**
   * Return a public profile — from cache if available, otherwise fetch.
   */
  async function getPublicProfile(userId: string): Promise<PublicProfile> {
    if (profileCache.value.has(userId)) {
      return profileCache.value.get(userId)!;
    }
    const profile = await userService.getPublicProfile(userId);
    profileCache.value.set(userId, profile);
    return profile;
  }

  /**
   * Search users by username query.
   */
  async function searchProfiles(query: string): Promise<PublicProfile[]> {
    return userService.searchProfiles(query);
  }

  /**
   * Fetch and store contact list.
   */
  async function fetchContacts(): Promise<void> {
    contacts.value = await userService.getContacts();
  }

  /**
   * Add a user to contacts.
   */
  async function addContact(userId: string): Promise<void> {
    const contact = await userService.addContact(userId);
    contacts.value.push(contact);
  }

  /**
   * Remove a contact by contact record ID.
   */
  async function removeContact(contactId: string): Promise<void> {
    await userService.removeContact(contactId);
    contacts.value = contacts.value.filter((c) => c.id !== contactId);
  }

  /**
   * Block a user and remove from contacts list.
   */
  async function blockUser(userId: string): Promise<void> {
    await userService.blockUser(userId);
    contacts.value = contacts.value.filter((c) => c.contact.id !== userId);
  }

  return {
    ownProfile,
    contacts,
    profileCache,
    fetchOwnProfile,
    createProfile,
    updateProfile,
    getPublicProfile,
    searchProfiles,
    fetchContacts,
    addContact,
    removeContact,
    blockUser,
  };
});
