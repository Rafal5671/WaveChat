import api from "./api";
import type { AuthTokens } from "@/types";

/**
 * Handles all communication with auth_service via API Gateway.
 */
export const authService = {
  /**
   * Send OTP to the provided phone number.
   */
  async register(
    phoneNumber: string,
    password: string,
  ): Promise<{ message: string; phone_number: string }> {
    const { data } = await api.post("/api/auth/register/", {
      phone_number: phoneNumber,
      password,
    });
    return data;
  },

  /**
   * Verify OTP and complete registration. Returns JWT tokens.
   */
  async verifyPhone(phoneNumber: string, code: string): Promise<AuthTokens> {
    const { data } = await api.post("/api/auth/verify-phone/", {
      phone_number: phoneNumber,
      code,
    });
    return data;
  },

  /**
   * Login with phone number and password. Returns JWT tokens.
   */
  async login(phoneNumber: string, password: string): Promise<AuthTokens> {
    const { data } = await api.post("/api/auth/login/", {
      phone_number: phoneNumber,
      password,
    });
    return data;
  },

  /**
   * Blacklist refresh token and clear local storage.
   */
  async logout(): Promise<void> {
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      await api.post("/api/auth/logout/", { refresh: refreshToken });
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_id");
  },

  /**
   * Persist tokens to localStorage after login or registration.
   */
  saveTokens(tokens: AuthTokens): void {
    localStorage.setItem("access_token", tokens.access);
    localStorage.setItem("refresh_token", tokens.refresh);
    localStorage.setItem("user_id", tokens.user_id);
  },

  /**
   * Check whether the user has a valid access token in localStorage.
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem("access_token");
  },

  /**
   * Return the current user ID from localStorage.
   */
  getUserId(): string | null {
    return localStorage.getItem("user_id");
  },
};
