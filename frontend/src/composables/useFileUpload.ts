import { ref } from "vue";
import { mediaService } from "@/services/media.service";
import type { MediaUploadResponse } from "@/types";

/**
 * Composable for handling file uploads to media_service.
 * Tracks upload progress and exposes the result.
 */
export function useFileUpload() {
  const isUploading = ref(false);
  const uploadError = ref<string | null>(null);

  /**
   * Upload a file and return its metadata.
   * Sets isUploading during the request and captures any errors.
   */
  async function upload(file: File): Promise<MediaUploadResponse | null> {
    isUploading.value = true;
    uploadError.value = null;

    try {
      const mediaType = mediaService.getMediaType(file);
      return await mediaService.upload(file, mediaType);
    } catch {
      uploadError.value = "File upload failed. Please try again.";
      return null;
    } finally {
      isUploading.value = false;
    }
  }

  return {
    isUploading,
    uploadError,
    upload,
  };
}
