// src/components/auth/PublicRoute.tsx
import { Navigate, Outlet } from "react-router-dom";
import { useStore } from "@nanostores/react";
import { $isAuthenticated, $isAuthLoading } from "@/store/authStore";

export function PublicRoute() {
  const isAuthenticated = useStore($isAuthenticated);
  const isAuthLoading = useStore($isAuthLoading);

  // Show loading spinner while checking authentication status
  if (isAuthLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
      </div>
    );
  }

  // If user is already authenticated, redirect them away from public pages (login/signup)
  // to their dashboard or main app area
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  // If not authenticated, allow access to public routes (login, signup, landing page, etc.)
  return <Outlet />;
}
