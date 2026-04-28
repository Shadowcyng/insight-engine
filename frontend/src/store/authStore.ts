// src/store/authStore.ts
import { atom } from "nanostores";

// Minor comment: Define the shape of your FastAPI user data
export interface User {
  id: number;
  email: string;
  role: { name: string; id: number };
}

// Minor comment: The actual user object
export const $user = atom<User | null>(null);
export const $accessToken = atom<string | null>(null);

// Minor comment: Computed boolean for easy routing checks (e.g., redirecting to /login)
export const $isAuthenticated = atom<boolean>(false);

// Minor comment: Crucial for the initial app load to prevent flashing the login screen
export const $isAuthLoading = atom<boolean>(true);

// Minor comment: Global action to update the user and auth state simultaneously
export function setUser(user: User | null, token: string | null = null) {
  $user.set(user);
  $accessToken.set(token);
  $isAuthenticated.set(!!user);
}
