import { create } from "zustand";

interface UIState {
  mobileSidebarOpen: boolean;
  desktopSidebarCollapsed: boolean;
  setMobileSidebarOpen: (open: boolean) => void;
  toggleMobileSidebar: () => void;
  toggleDesktopSidebar: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  mobileSidebarOpen: false,
  desktopSidebarCollapsed: false,
  setMobileSidebarOpen: (open) => set({ mobileSidebarOpen: open }),
  toggleMobileSidebar: () =>
    set((state) => ({ mobileSidebarOpen: !state.mobileSidebarOpen })),
  toggleDesktopSidebar: () =>
    set((state) => ({ desktopSidebarCollapsed: !state.desktopSidebarCollapsed })),
}));
