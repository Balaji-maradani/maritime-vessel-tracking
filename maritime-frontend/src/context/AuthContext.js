import { createContext, useContext, useState, useEffect, useCallback } from "react";
import axios from "axios";

const AuthContext = createContext();

// API base URL from environment variable
const API_BASE_URL = process.env.REACT_APP_API_BASE || 'https://maritime-backend-q150.onrender.com';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => {
    // Initialize token from localStorage
    return localStorage.getItem("access") || null;
  });

  const logout = useCallback(() => {
    // Clear tokens from localStorage
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    setUser(null);
    setToken(null);
  }, []);

  // Load user info when token is available
  useEffect(() => {
    if (token) {
      axios
        .get(`${API_BASE_URL}/api/me/`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        .then((res) => setUser(res.data))
        .catch(() => logout());
    } else {
      setUser(null);
    }
  }, [token, logout]);

  const login = async (username, password) => {
    try {
      const res = await axios.post(`${API_BASE_URL}/api/token/`, {
        username,
        password,
      });

      // Persist tokens in localStorage
      localStorage.setItem("access", res.data.access);
      if (res.data.refresh) {
        localStorage.setItem("refresh", res.data.refresh);
      }
      setToken(res.data.access);
      
      // Return the token for role validation
      return res.data.access;
    } catch (error) {
      throw error;
    }
  };

  const fetchUserData = async (token) => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/me/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return res.data;
    } catch (error) {
      throw error;
    }
  };

  const register = async (username, email, password, role = "OPERATOR") => {
    try {
      const res = await axios.post(`${API_BASE_URL}/api/register/`, {
        username,
        email,
        password,
        role,
      });

      // After successful registration, automatically log in the user
      if (res.data.access || res.data.token) {
        const accessToken = res.data.access || res.data.token;
        localStorage.setItem("access", accessToken);
        if (res.data.refresh) {
          localStorage.setItem("refresh", res.data.refresh);
        }
        setToken(accessToken);
      }

      return res.data;
    } catch (error) {
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, register, fetchUserData }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
