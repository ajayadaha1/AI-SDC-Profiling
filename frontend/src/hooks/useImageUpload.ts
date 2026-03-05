import { useCallback } from 'react';
import { useChatStore } from '../stores/chatStore';

const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/bmp'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function useImageUpload() {
  const { addPendingImage, removePendingImage, pendingImages, clearPendingImages } = useChatStore();

  const validateAndAdd = useCallback(
    (files: FileList | File[]) => {
      const fileArray = Array.from(files);
      for (const file of fileArray) {
        if (!ACCEPTED_TYPES.includes(file.type)) continue;
        if (file.size > MAX_FILE_SIZE) continue;
        if (pendingImages.length >= 5) break; // Max 5 images
        addPendingImage(file);
      }
    },
    [addPendingImage, pendingImages.length],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (e.dataTransfer.files.length > 0) {
        validateAndAdd(e.dataTransfer.files);
      }
    },
    [validateAndAdd],
  );

  const handlePaste = useCallback(
    (e: React.ClipboardEvent) => {
      const files = e.clipboardData.files;
      if (files.length > 0) {
        validateAndAdd(files);
      }
    },
    [validateAndAdd],
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        validateAndAdd(e.target.files);
        e.target.value = ''; // Reset so same file can be selected again
      }
    },
    [validateAndAdd],
  );

  return {
    pendingImages,
    handleDrop,
    handlePaste,
    handleFileSelect,
    removePendingImage,
    clearPendingImages,
  };
}
