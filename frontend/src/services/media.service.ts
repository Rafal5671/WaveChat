import api from "./api";
import type { MediaUploadResponse } from "@/types";

/**
 * Handles file uploads to media_service via API Gateway.
 */
export const mediaService = {
  /**
   * Upload a file and return its URL and metadata.
   * Accepts image, video, audio or file as media_type.
   */
  async upload(
    file: File,
    mediaType: "image" | "video" | "audio" | "file" = "file",
  ): Promise<MediaUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("media_type", mediaType);

    const { data } = await api.post("/api/media/upload/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  /**
   * Determine media type from a File object MIME type.
   */
  getMediaType(file: File): "image" | "video" | "audio" | "file" {
    if (file.type.startsWith("image/")) return "image";
    if (file.type.startsWith("video/")) return "video";
    if (file.type.startsWith("audio/")) return "audio";
    return "file";
  },
};
