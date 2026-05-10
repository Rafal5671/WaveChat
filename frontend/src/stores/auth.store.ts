import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { authService } from "@/services/auth.service";
import type { AuthTokens } from "@/types";

/**
 * Manages authentication state — tokens, user ID and login status.
 * Persists tokens to localStorage via authService.
 */
export const useAuthStore = defineStore("auth", () => {
  const userId = ref<string | null>(localStorage.getItem("user_id"));
  const accessToken = ref<string | null>(localStorage.getItem("access_token"));

  const isAuthenticated = computed(() => !!accessToken.value);

  /**
   * Register a new user and send OTP.
   */
  async function register(phoneNumber: string, password: string) {
    return authService.register(phoneNumber, password);
  }

  /**
   * Verify OTP, save tokens and update store state.
   */
  async function verifyEmail(email: string, code: string) {
    const tokens: AuthTokens = await authService.verifyEmail(email, code);
    _applyTokens(tokens);
  }

  /**
   * Login with email and password, save tokens and update store state.
   */
  async function login(email: string, password: string) {
    const tokens: AuthTokens = await authService.login(email, password);
    _applyTokens(tokens);
  }

  /**
   * Logout — blacklist token, clear store and localStorage.
   */
  async function logout() {
    await authService.logout();
    accessToken.value = null;
    userId.value = null;
  }

  function _applyTokens(tokens: AuthTokens) {
    authService.saveTokens(tokens);
    accessToken.value = tokens.access;
    userId.value = tokens.user_id;
  }

  return {
    userId,
    accessToken,
    isAuthenticated,
    register,
    verifyPhone,
    login,
    logout,
  };
});
