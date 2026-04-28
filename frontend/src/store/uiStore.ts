import { atom, map } from "nanostores";

export type ThemeMode = "light" | "dark" | "system";

interface UiState {
  theme: ThemeMode;
  isSidebarOpen: boolean;
}

export const $ui = map<UiState>({
  theme: "system",
  isSidebarOpen: false,
});

// Minor comment: Derived state using 'computed' (if needed later) or simple action functions
export function toggleSidebar() {
  const currentState = $ui.get();
  $ui.setKey("isSidebarOpen", !currentState.isSidebarOpen);
}

export function setTheme(newTheme: ThemeMode) {
  $ui.setKey("theme", newTheme);
  // Minor comment: You would also inject the theme class into the HTML document root here
}
