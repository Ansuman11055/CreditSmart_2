// Phase 4D+ Local Auth - Password-based Authentication Context Provider
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { 
  restoreSession, 
  signOut as authSignOut,
  signIn as authSignIn,
  signUp as authSignUp,
  updateUserCurrency
} from '../services/authService';

export interface User {
  id: string;
  name: string;
  email: string;
  currency: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  signIn: (email: string, password: string, rememberMe?: boolean) => Promise<{ success: boolean; error?: string }>;
  signUp: (name: string, email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signOut: () => void;
  updateCurrency: (currency: string) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    isLoading: true
  });

  // Phase 4D+ Local Auth - Auto-login on app mount (restore session)
  useEffect(() => {
    try {
      const session = restoreSession();
      
      if (session) {
        // Phase 4D+ Local Auth - Session found, auto-authenticate
        setAuthState({
          isAuthenticated: true,
          user: {
            id: session.userId,
            name: session.name,
            email: session.email,
            currency: session.currency
          },
          isLoading: false
        });
        console.log('Session restored successfully');
      } else {
        // Phase 4D+ Local Auth - No session found
        setAuthState({
          isAuthenticated: false,
          user: null,
          isLoading: false
        });
      }
    } catch (error) {
      console.error('Failed to restore session:', error);
      setAuthState({
        isAuthenticated: false,
        user: null,
        isLoading: false
      });
    }
  }, []);

  // Phase 4D+ Local Auth - Sign in with password
  const signIn = useCallback(async (
    email: string, 
    password: string, 
    rememberMe: boolean = false
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const result = await authSignIn(email, password, rememberMe);
      
      if (result.success && result.user) {
        // Phase 4D+ Local Auth - Update auth state
        setAuthState({
          isAuthenticated: true,
          user: {
            id: result.user.userId,
            name: result.user.name,
            email: result.user.email,
            currency: result.user.currency
          },
          isLoading: false
        });
        
        return { success: true };
      } else {
        return { success: false, error: result.error || 'Sign in failed' };
      }
    } catch (error) {
      console.error('Sign in error:', error);
      return { success: false, error: 'An unexpected error occurred' };
    }
  }, []);

  // Phase 4D+ Local Auth - Sign up with password
  const signUp = useCallback(async (
    name: string,
    email: string,
    password: string
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const result = await authSignUp(name, email, password);
      return result;
    } catch (error) {
      console.error('Sign up error:', error);
      return { success: false, error: 'An unexpected error occurred' };
    }
  }, []);

  // Phase 4D+ Local Auth - Sign out user
  const signOut = useCallback(() => {
    authSignOut();
    setAuthState({
      isAuthenticated: false,
      user: null,
      isLoading: false
    });
  }, []);

  // Phase 4D+ Local Auth - Update user currency preference
  const updateCurrency = useCallback((currency: string) => {
    if (authState.user) {
      updateUserCurrency(authState.user.email, currency);
      setAuthState(prev => ({
        ...prev,
        user: prev.user ? { ...prev.user, currency } : null
      }));
    }
  }, [authState.user]);

  return (
    <AuthContext.Provider value={{
      ...authState,
      signIn,
      signUp,
      signOut,
      updateCurrency
    }}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Hook to access auth context
 * @throws Error if used outside AuthProvider
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

/**
 * Get user-specific localStorage key for namespacing data
 */
export function getUserStorageKey(userId: string, key: string): string {
  return `creditsmart_user_${userId}_${key}`;
}
