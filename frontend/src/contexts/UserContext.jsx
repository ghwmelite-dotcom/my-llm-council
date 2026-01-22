import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('llm-council-token');
    if (storedToken) {
      setToken(storedToken);
      fetchCurrentUser(storedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  // Fetch current user from token
  const fetchCurrentUser = async (authToken) => {
    try {
      const response = await fetch(`${API_URL}/api/auth/me`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        // Token invalid, clear it
        localStorage.removeItem('llm-council-token');
        setToken(null);
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      localStorage.removeItem('llm-council-token');
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Login handler - called after successful auth
  const login = useCallback((authToken, userData) => {
    localStorage.setItem('llm-council-token', authToken);
    setToken(authToken);
    setUser(userData);
    setIsAuthenticated(true);
  }, []);

  // Logout handler
  const logout = useCallback(() => {
    localStorage.removeItem('llm-council-token');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  // Update user profile
  const updateProfile = useCallback(async (updates) => {
    if (!token) return null;

    try {
      const response = await fetch(`${API_URL}/api/auth/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updates),
      });

      if (response.ok) {
        const updatedUser = await response.json();
        setUser((prev) => ({ ...prev, ...updatedUser }));
        return updatedUser;
      }
      return null;
    } catch (error) {
      console.error('Failed to update profile:', error);
      return null;
    }
  }, [token]);

  // Complete onboarding
  const completeOnboarding = useCallback(async () => {
    if (!token) return false;

    try {
      const response = await fetch(`${API_URL}/api/auth/onboarding`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ complete: true }),
      });

      if (response.ok) {
        setUser((prev) => ({ ...prev, onboarding_complete: true }));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      return false;
    }
  }, [token]);

  // Get auth header for API requests
  const getAuthHeader = useCallback(() => {
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
  }, [token]);

  const value = {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    logout,
    updateProfile,
    completeOnboarding,
    getAuthHeader,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}

export default UserContext;
