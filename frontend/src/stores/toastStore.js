// Zustand store for toast notifications
import { create } from 'zustand';

let toastId = 0;

export const useToastStore = create((set, get) => ({
  toasts: [],

  // Add a toast notification
  addToast: ({ type = 'info', message, duration = 4000 }) => {
    const id = ++toastId;

    set((state) => ({
      toasts: [...state.toasts, { id, type, message }],
    }));

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        get().removeToast(id);
      }, duration);
    }

    return id;
  },

  // Remove a specific toast
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },

  // Clear all toasts
  clearToasts: () => {
    set({ toasts: [] });
  },

  // Convenience methods
  success: (message, duration) =>
    get().addToast({ type: 'success', message, duration }),

  error: (message, duration = 6000) =>
    get().addToast({ type: 'error', message, duration }),

  info: (message, duration) =>
    get().addToast({ type: 'info', message, duration }),

  warning: (message, duration = 5000) =>
    get().addToast({ type: 'warning', message, duration }),
}));

// Hook for easy access to toast functions
export const useToast = () => {
  const { success, error, info, warning } = useToastStore();
  return { success, error, info, warning };
};
