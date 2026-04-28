// src/api/authApi.ts
import { apiClient } from "./apiClient";
import { type User } from "@/store/authStore";

// Minor comment: Pure function to handle the login request.
// It takes raw credentials and returns the User object.
export const loginUser = async (
  username: string,
  password: string,
): Promise<User> => {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);
  const response = await apiClient.post("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
  return response.data;
};
