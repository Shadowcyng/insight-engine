// src/components/auth/ProtectedRoute.tsx
import { Navigate, Outlet } from "react-router-dom";
import { useStore } from "@nanostores/react";
import { $isAuthenticated, $isAuthLoading } from "@/store/authStore";

export function ProtectedRoute() {
  const isAuthenticated = useStore($isAuthenticated);
  const isAuthLoading = useStore($isAuthLoading);

  // Minor comment: Show nothing or a sleek spinner while Nginx checks the HttpOnly cookie
  if (isAuthLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
      </div>
    );
  }

  // Minor comment: If the cookie check failed, kick them to the login URL
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Minor comment: If authenticated, render the child routes (e.g., Dashboard)
  return <Outlet />;
}
