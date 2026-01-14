import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // Role-based visibility helpers
  const canAccessDashboard = () => {
    // All authenticated users can access dashboard
    return !!user;
  };

  const canAccessVessels = () => {
    // Customize based on role - example: OPERATOR and ANALYST can access vessels
    if (!user) return false;
    const role = user.role?.toUpperCase();
    return role === "OPERATOR" || role === "ANALYST" || role === "ADMIN";
  };

  const canAccessAnalytics = () => {
    // ANALYST and ADMIN can access full analytics, OPERATOR gets basic analytics
    if (!user) return false;
    const role = user.role?.toUpperCase();
    return role === "OPERATOR" || role === "ANALYST" || role === "ADMIN";
  };

  const canAccessPorts = () => {
    // All authenticated users can access ports dashboard
    if (!user) return false;
    const role = user.role?.toUpperCase();
    return role === "OPERATOR" || role === "ANALYST" || role === "ADMIN";
  };

  const getUserDisplayName = () => {
    if (!user) return "";
    return user.username || user.email || "User";
  };

  const getUserRole = () => {
    if (!user) return "";
    return user.role || "";
  };

  return (
    <div className="navbar bg-primary px-6">
      {/* LEFT */}
      <div className="flex-1">
        <Link to="/" className="text-white text-xl font-bold">
          Maritime Tracker
        </Link>
      </div>

      {/* RIGHT */}
      <div className="flex gap-4 items-center">
        {user ? (
          <>
            {/* User info */}
            <span className="text-white text-sm">
              {getUserDisplayName()}
              {getUserRole() && (
                <span className="ml-2 opacity-80">({getUserRole()})</span>
              )}
            </span>

            {/* Dashboard - visible to all authenticated users */}
            {canAccessDashboard() && (
              <Link to="/" className="btn btn-sm btn-ghost text-white">
                Dashboard
              </Link>
            )}

            {/* Vessels - visible based on role */}
            {canAccessVessels() && (
              <Link to="/vessels" className="btn btn-sm btn-ghost text-white">
                Vessels
              </Link>
            )}

            {/* Analytics - visible based on role */}
            {canAccessAnalytics() && (
              <Link to="/analytics" className="btn btn-sm btn-ghost text-white">
                Analytics
              </Link>
            )}

            {/* Ports - visible based on role */}
            {canAccessPorts() && (
              <Link to="/ports" className="btn btn-sm btn-ghost text-white">
                Ports
              </Link>
            )}

            {/* Logout - visible to all authenticated users */}
            <button
              className="btn btn-sm btn-error text-white"
              onClick={handleLogout}
            >
              Logout
            </button>
          </>
        ) : (
          <>
            {/* Login/Register - visible when not authenticated */}
            <Link to="/login" className="btn btn-sm btn-ghost text-white">
              Login
            </Link>
            <Link to="/register" className="btn btn-sm btn-ghost text-white">
              Register
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
