import api from "./api";
import type { Contact, Profile, PublicProfile } from "@/types";

/**
 * Handles all communication with user_service via API Gateway.
 */
export const userService = {
  /**
   * Create a profile after registration.
   */
  async createProfile(username: string, displayName: string): Promise<Profile> {
    const { data } = await api.post("/api/users/profile/create/", {
      username,
      display_name: displayName,
    });
    return data;
  },

  /**
   * Return own profile data.
   */
  async getOwnProfile(): Promise<Profile> {
    const { data } = await api.get("/api/users/profile/");
    return data;
  },

  /**
   * Partially update own profile.
   */
  async updateProfile(
    payload: Partial<Pick<Profile, "username" | "display_name" | "bio" | "avatar_url">>,
  ): Promise<Profile> {
    const { data } = await api.patch("/api/users/profile/", payload);
    return data;
  },

  /**
   * Return public profile for a given user ID.
   */
  async getPublicProfile(userId: string): Promise<PublicProfile> {
    const { data } = await api.get(`/api/users/profile/${userId}/`);
    return data;
  },

  /**
   * Search users by username.
   */
  async searchProfiles(query: string): Promise<PublicProfile[]> {
    const { data } = await api.get("/api/users/profile/search/", {
      params: { q: query },
    });
    return data;
  },

  /**
   * Return all contacts for the current user.
   */
  async getContacts(): Promise<Contact[]> {
    const { data } = await api.get("/api/users/contacts/");
    return data;
  },

  /**
   * Add a user to contacts by user ID.
   */
  async addContact(userId: string): Promise<Contact> {
    const { data } = await api.post("/api/users/contacts/", { user_id: userId });
    return data;
  },

  /**
   * Remove a contact by contact record ID.
   */
  async removeContact(contactId: string): Promise<void> {
    await api.delete(`/api/users/contacts/${contactId}/`);
  },

  /**
   * Block a user by user ID.
   */
  async blockUser(userId: string): Promise<void> {
    await api.post(`/api/users/contacts/block/${userId}/`);
  },

  /**
   * Unblock a user by user ID.
   */
  async unblockUser(userId: string): Promise<void> {
    await api.delete(`/api/users/contacts/block/${userId}/`);
  },
};
