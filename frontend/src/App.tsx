// src/App.tsx
import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { $isAuthLoading, setUser } from "@/store/authStore";
import { apiClient } from "@/api/apiClient";
import { Login } from "@/components/auth/Login";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { PublicRoute } from "./components/auth/PublicRoute";
import { Canvas } from "./components/dashboard/Canvas";

// Minor comment: A placeholder for your protected interface

export default function App() {
  // Minor comment: Run the session check once when the app mounts
  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await apiClient.get("/auth/me");
        setUser(response.data.user);
      } catch (error) {
        setUser(null);
      } finally {
        $isAuthLoading.set(false);
      }
    };
    checkSession();
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        {/* Minor comment: Public Routes */}
        <Route element={<PublicRoute />}>
          <Route path="/login" element={<Login />} />
        </Route>

        {/* Minor comment: All routes inside here require the HttpOnly cookie */}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Canvas />} />
          <Route path="/settings" element={<div>Settings Page</div>} />
        </Route>

        {/* Minor comment: Catch-all for 404s */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
