import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children, roles }) {
  const { user, token } = useAuth();

  // If no token exists, redirect to login immediately
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // If token exists but user data is not loaded yet, show loading
  // (This handles the case where token is being validated)
  if (token && !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  // If user exists but doesn't have required role, redirect
  if (roles && user && !roles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  // User is authenticated and has required role (if specified)
  return children;
}
