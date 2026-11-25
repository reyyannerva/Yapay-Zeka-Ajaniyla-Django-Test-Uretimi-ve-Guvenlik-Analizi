import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import type { User } from '../types';
import { logout } from './api/auth';

export interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  /** Mock giriş: gerçek token akışı #41'de bağlanacak. */
  signInMock: (user: User) => void;
  signOut: () => void;
  /** Süresi dolan oturum (ör. 401): kullanıcıyı temizler, ProtectedRoute /login'e yönlendirir. */
  expireSession: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  children: ReactNode;
  /** Yalnızca test/geliştirme için başlangıç kullanıcısı. */
  initialUser?: User | null;
}

export function AuthProvider({ children, initialUser = null }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(initialUser);

  const signInMock = useCallback((next: User) => setUser(next), []);

  const signOut = useCallback(() => {
    setUser(null);
    // Gerçek servis (#41) hatası oturumu kapatmayı engellemez.
    void logout().catch(() => undefined);
  }, []);

  const expireSession = useCallback(() => setUser(null), []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: user !== null, signInMock, signOut, expireSession }),
    [user, signInMock, signOut, expireSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth, AuthProvider içinde kullanılmalıdır');
  return ctx;
}
