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
  /** Oturum süresi doldu (ör. 401 yanıtı): kullanıcı temizlenir, ProtectedRoute /session-expired'a yönlendirir. */
  sessionExpired: boolean;
  expireSession: () => void;
  /** Oturum-sonu bildirimini kapatır (kullanıcı yeniden girişe yöneldi); sonraki yönlendirmeler /login'e gider. */
  dismissSessionExpired: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  children: ReactNode;
  /** Yalnızca test/geliştirme için başlangıç kullanıcısı. */
  initialUser?: User | null;
}

export function AuthProvider({ children, initialUser = null }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(initialUser);
  const [sessionExpired, setSessionExpired] = useState(false);

  const signInMock = useCallback((next: User) => {
    setUser(next);
    setSessionExpired(false);
  }, []);

  const signOut = useCallback(() => {
    setUser(null);
    setSessionExpired(false);
    // Gerçek servis (#41) hatası oturumu kapatmayı engellemez.
    void logout().catch(() => undefined);
  }, []);

  const expireSession = useCallback(() => {
    setUser(null);
    setSessionExpired(true);
  }, []);

  const dismissSessionExpired = useCallback(() => {
    setUser(null);
    setSessionExpired(false);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      signInMock,
      signOut,
      sessionExpired,
      expireSession,
      dismissSessionExpired,
    }),
    [user, signInMock, signOut, sessionExpired, expireSession, dismissSessionExpired],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth, AuthProvider içinde kullanılmalıdır');
  return ctx;
}
