'use client';

/**
 * Auth Context
 *
 * Manages authentication state, JWT token, and user session
 */

import * as React from 'react';
import api from '../services/api';
import { useRouter } from 'next/navigation';

interface User {
  id: number;
  email: string;
  name: string;
  is_admin: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [token, setToken] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const router = useRouter();

  // Initialize auth state from localStorage on mount
  React.useEffect(() => {
    const storedToken = localStorage.getItem('admin_token');
    const storedUser = localStorage.getItem('admin_user');

    if (storedToken && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setToken(storedToken);
        setUser(parsedUser);
        api.setAuthToken(storedToken);
      } catch (err) {
        console.error('Failed to parse stored user:', err);
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_user');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await api.post<{ access_token: string; user: any }>('/v1/login', {
        email,
        password,
      });

      const { access_token } = response;

      // Decode JWT to get user info (basic decode, not validation)
      const payload = JSON.parse(atob(access_token.split('.')[1]));

      const userData: User = {
        id: payload.id,
        email: email,
        name: payload.name || email,
        is_admin: payload.is_admin || false,
      };

      // Store in state and localStorage
      setToken(access_token);
      setUser(userData);
      localStorage.setItem('admin_token', access_token);
      localStorage.setItem('admin_user', JSON.stringify(userData));

      // Set token in API service
      api.setAuthToken(access_token);
    } catch (err: any) {
      console.error('Login failed:', err);
      throw new Error(err.message || 'Login failed. Please check your credentials.');
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    api.clearAuthToken();
    router.push('/login');
  };

  const checkAuth = async (): Promise<boolean> => {
    if (!token) return false;

    try {
      // Try to fetch dashboard stats to verify token is valid and user is admin
      await api.get('/v1/admin/stats');
      return true;
    } catch (err) {
      // Token is invalid or user is not admin
      logout();
      return false;
    }
  };

  const value = {
    user,
    token,
    isLoading,
    login,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
