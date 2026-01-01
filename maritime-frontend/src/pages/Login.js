import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(""); // Optional UI display only
  const [error, setError] = useState("");
  const [errorType, setErrorType] = useState(""); // 'auth' or 'role'
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { login, fetchUserData } = useAuth();
  const navigate = useNavigate();

  // Auto-clear error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError("");
        setErrorType("");
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [error]);

  const setAuthError = (message) => {
    setError(message);
    setErrorType("auth");
  };

  const clearError = () => {
    setError("");
    setErrorType("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    setLoading(true);

    // Validate inputs - role is now optional for UI display only
    if (!username.trim() || !password.trim()) {
      setAuthError("Please fill in username and password");
      setLoading(false);
      return;
    }

    try {
      // Step 1: Authenticate with username and password only
      const token = await login(username, password);
      
      // Step 2: Fetch user data to get actual role from backend
      await fetchUserData(token);
      
      // Step 3: Route user based on backend role (no validation against selected role)
      // The backend role is the authoritative source
      navigate("/");
    } catch (err) {
      // Handle authentication errors (username/password incorrect)
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || "";
      
      if (errorMessage.toLowerCase().includes("invalid credentials") || 
          errorMessage.toLowerCase().includes("no active account") ||
          errorMessage.toLowerCase().includes("unable to log in")) {
        setAuthError("Invalid username or password. Please check your credentials and try again.");
      } else {
        setAuthError(
          errorMessage ||
          "Login failed. Please try again."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
        {/* Animated particles */}
        <div className="absolute inset-0">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="absolute w-2 h-2 bg-blue-400/20 rounded-full animate-pulse"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 3}s`,
                animationDuration: `${3 + Math.random() * 2}s`
              }}
            />
          ))}
        </div>
        
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-black/30" />
      </div>

      {/* Content */}
      <div className="relative z-10 flex items-center justify-center px-4 py-12 min-h-screen">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center w-full max-w-6xl">

          {/* Left Side — Info Panel */}
          <div className="space-y-8 text-white order-2 lg:order-1">
            <div className="space-y-4">
              <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
                Maritime Operations Control
              </h1>
              <p className="text-xl text-blue-100/80 leading-relaxed">
                Access your maritime tracking dashboard with real-time vessel monitoring, safety alerts & operational insights.
              </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="group p-6 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/15 transition-all duration-300 hover:scale-105">
                <h2 className="text-3xl font-bold text-blue-300 group-hover:text-blue-200 transition-colors">524</h2>
                <p className="text-blue-100/70 text-sm mt-1">Active Vessels</p>
              </div>
              <div className="group p-6 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/15 transition-all duration-300 hover:scale-105">
                <h2 className="text-3xl font-bold text-green-300 group-hover:text-green-200 transition-colors">89</h2>
                <p className="text-blue-100/70 text-sm mt-1">Live Tracking</p>
              </div>
              <div className="group p-6 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/15 transition-all duration-300 hover:scale-105">
                <h2 className="text-3xl font-bold text-purple-300 group-hover:text-purple-200 transition-colors">142</h2>
                <p className="text-blue-100/70 text-sm mt-1">Global Ports</p>
              </div>
              <div className="group p-6 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/15 transition-all duration-300 hover:scale-105">
                <h2 className="text-3xl font-bold text-red-300 group-hover:text-red-200 transition-colors">7</h2>
                <p className="text-blue-100/70 text-sm mt-1">Active Alerts</p>
              </div>
            </div>

            <div className="flex items-center gap-3 text-blue-100/60">
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-cyan-400 flex items-center justify-center">
                <span className="text-white text-sm">🚀</span>
              </div>
              <p className="text-sm">
                Trusted by maritime professionals for safe and efficient ocean operations.
              </p>
            </div>
          </div>

          {/* Right Side — Login Form */}
          <div className="order-1 lg:order-2">
            <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl p-8 lg:p-10 border border-white/20">
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-gray-800 mb-2">Welcome Back</h2>
                <p className="text-gray-600">Sign in to your maritime control center</p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Username Field */}
                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    <span className="flex items-center gap-2">
                      <span className="text-blue-600">👤</span>
                      Username
                    </span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Enter your username"
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:bg-gray-100"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      disabled={loading}
                      required
                    />
                  </div>
                </div>

                {/* Password Field */}
                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    <span className="flex items-center gap-2">
                      <span className="text-blue-600">🔒</span>
                      Password
                    </span>
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      placeholder="Enter your password"
                      className="w-full px-4 py-3 pr-12 bg-gray-50 border border-gray-200 rounded-xl text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:bg-gray-100"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      disabled={loading}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                      disabled={loading}
                    >
                      {showPassword ? (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      )}
                    </button>
                  </div>
                </div>

                {/* Role Field - Optional UI Display */}
                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700">
                    <span className="flex items-center gap-2">
                      <span className="text-blue-600">🎯</span>
                      Role <span className="text-gray-400 text-xs font-normal">(optional)</span>
                    </span>
                  </label>
                  <div className="relative">
                    <select
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:bg-gray-100 appearance-none cursor-pointer"
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      disabled={loading}
                    >
                      <option value="">Select role (optional)</option>
                      <option value="OPERATOR">Operator</option>
                      <option value="ANALYST">Analyst</option>
                      <option value="ADMIN">Admin</option>
                    </select>
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500">
                    Your actual role will be determined by your account settings
                  </p>
                </div>

                {/* Enhanced Error Message */}
                {error && (
                  <div className={`p-4 rounded-xl border transition-all duration-300 ${
                    errorType === 'role' 
                      ? 'bg-orange-50 border-orange-200' 
                      : 'bg-red-50 border-red-200'
                  }`}>
                    <div className="flex items-start gap-3">
                      {/* Different icons for different error types */}
                      {errorType === 'role' ? (
                        <svg className="w-5 h-5 text-orange-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )}
                      
                      <div className="flex-1">
                        <span className={`text-sm font-medium ${
                          errorType === 'role' ? 'text-orange-700' : 'text-red-700'
                        }`}>
                          {error}
                        </span>
                        
                        {/* Additional context for role mismatch */}
                        {errorType === 'role' && (
                          <p className="text-xs text-orange-600 mt-1">
                            Please select the correct role from the dropdown above and try again.
                          </p>
                        )}
                      </div>
                      
                      {/* Close button */}
                      <button
                        type="button"
                        onClick={clearError}
                        className={`p-1 rounded-full hover:bg-opacity-20 transition-colors ${
                          errorType === 'role' 
                            ? 'text-orange-400 hover:bg-orange-500' 
                            : 'text-red-400 hover:bg-red-500'
                        }`}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                    
                    {/* Auto-clear progress indicator */}
                    <div className={`mt-3 h-1 rounded-full overflow-hidden ${
                      errorType === 'role' ? 'bg-orange-200' : 'bg-red-200'
                    }`}>
                      <div 
                        className={`h-full rounded-full ${
                          errorType === 'role' ? 'bg-orange-400' : 'bg-red-400'
                        }`}
                        style={{ 
                          width: '100%',
                          animation: 'shrinkWidth 5s linear forwards'
                        }}
                      />
                    </div>
                  </div>
                )}
                
                {/* CSS Animation for progress bar */}
                <style dangerouslySetInnerHTML={{
                  __html: `
                    @keyframes shrinkWidth {
                      from { width: 100%; }
                      to { width: 0%; }
                    }
                  `
                }} />

                {/* Submit Button */}
                <button
                  type="submit"
                  className="w-full py-3 px-6 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  disabled={loading}
                >
                  {loading ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Signing In...</span>
                    </div>
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      <span>Sign In to Dashboard</span>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </span>
                  )}
                </button>
              </form>

              {/* Footer */}
              <div className="mt-8 text-center">
                <p className="text-gray-600 text-sm">
                  Don't have an account?{" "}
                  <button
                    onClick={() => navigate("/register")}
                    className="text-blue-600 hover:text-blue-700 font-semibold hover:underline transition-colors duration-200"
                  >
                    Create Account
                  </button>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
