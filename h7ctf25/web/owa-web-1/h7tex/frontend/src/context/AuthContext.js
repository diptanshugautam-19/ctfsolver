import React, { createContext, useState, useContext, useEffect } from 'react';
import jwtDecode from 'jwt-decode';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  // Initialize token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      try {
        const decoded = jwtDecode(storedToken);
        // Check if token is expired
        if (decoded.exp * 1000 > Date.now()) {
          setToken(storedToken);
          setUser(decoded);
        } else {
          // Token expired, remove it
          localStorage.removeItem('authToken');
        }
      } catch (e) {
        // Invalid token, remove it
        localStorage.removeItem('authToken');
      }
    }
    setLoading(false);
  }, []);
  
  const login = (newToken) => {
    try {
      const decoded = jwtDecode(newToken);
      localStorage.setItem('authToken', newToken);
      setToken(newToken);
      setUser(decoded);
    } catch (e) {
      console.error('Invalid token received:', e);
      logout();
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setToken(null);
    setUser(null);
  };
  
  const getUser = () => {
    if (!token) return null;
    try {
      const decoded = jwtDecode(token);
      // Check expiration
      if (decoded.exp * 1000 <= Date.now()) {
        logout();
        return null;
      }
      return decoded;
    } catch (e) {
      logout();
      return null;
    }
  };

  const value = {
    token,
    login,
    logout,
    user: user || getUser(),
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
