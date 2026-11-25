// Oturum durumu (H5-03 / #41): gerçek SimpleJWT girişi, sayfa yenilemede oturumun geri yüklenmesi,
// çıkış ve oturum sonu. Token'lar `tokenStore`'dadır; burada yalnızca kullanıcı ve durum tutulur.
// Kullanıcı değiştiğinde (giriş, çıkış, oturum sonu) TanStack Query önbelleği tamamen temizlenir; bir
// kullanıcının verisi diğerine kısa süreliğine bile gösterilmez.
import { QueryClientContext } from '@tanstack/react-query';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import type { LoginCredentials, User } from '../types';
import { getMe, login, logoutWithTokens } from './api/auth';
import { isApiError, onSessionExpired } from './api/client';
import { tokenStore } from './api/token-store';

/** checking: saklanan oturum sunucuda doğrulanıyor (korumalı içerik gösterilmez). */
export type AuthStatus = 'checking' | 'authenticated' | 'anonymous';

export interface AuthContextValue {
  user: User | null;
  status: AuthStatus;
  isAuthenticated: boolean;
  /** Gerçek giriş: token alınır, kullanıcı /api/auth/me/ ile doğrulanır. Hata ApiError olarak fırlatılır. */
  signIn: (credentials: LoginCredentials) => Promise<void>;
  /** Yerel oturumu hemen kapatır; refresh token'ı sunucuda kara listeye almayı dener. */
  signOut: () => void;
  /** Oturum süresi doldu (yenilenemeyen 401): ProtectedRoute /session-expired'a yönlendirir. */
  sessionExpired: boolean;
  expireSession: () => void;
  /** Oturum-sonu bildirimini kapatır; sonraki yönlendirmeler /login'e gider. */
  dismissSessionExpired: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  children: ReactNode;
  /** Yalnızca testler için başlangıç kullanıcısı (sunucu doğrulaması atlanır). */
  initialUser?: User | null;
}

export function AuthProvider({ children, initialUser = null }: AuthProviderProps) {
  const queryClient = useContext(QueryClientContext);
  const [user, setUser] = useState<User | null>(initialUser);
  const [status, setStatus] = useState<AuthStatus>(() =>
    initialUser ? 'authenticated' : tokenStore.hasSession() ? 'checking' : 'anonymous',
  );
  const [sessionExpired, setSessionExpired] = useState(false);

  const resetCache = useCallback(() => {
    if (!queryClient) return;
    void queryClient.cancelQueries();
    queryClient.clear();
  }, [queryClient]);

  // Sayfa yenilemesi: saklanan refresh token varsa oturum sunucuda doğrulanır.
  useEffect(() => {
    if (status !== 'checking') return undefined;
    const controller = new AbortController();
    const generation = tokenStore.generation();
    getMe(controller.signal)
      .then((me) => {
        if (controller.signal.aborted || generation !== tokenStore.generation()) return;
        setUser(me);
        setStatus('authenticated');
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        // 401: istemci oturumu zaten temizledi. Bağlantı hatasında token'lar korunur, kullanıcı girişe yönlenir.
        if (isApiError(error) && error.status !== 0) tokenStore.clear();
        setUser(null);
        setStatus('anonymous');
      });
    return () => controller.abort();
  }, [status]);

  const endSession = useCallback(
    (expired: boolean) => {
      tokenStore.clear();
      resetCache();
      setUser(null);
      setStatus('anonymous');
      setSessionExpired(expired);
    },
    [resetCache],
  );

  // Merkezi istemci refresh token'ın geçersiz olduğunu bildirdiğinde.
  useEffect(() => onSessionExpired(() => endSession(true)), [endSession]);

  const signIn = useCallback(
    async (credentials: LoginCredentials) => {
      const tokens = await login(credentials);
      tokenStore.clear(); // önceki oturumdan kalan her şey (ve bekleyen yenilemeler) geçersiz
      resetCache();
      tokenStore.setTokens(tokens);
      try {
        const me = await getMe();
        setUser(me);
        setStatus('authenticated');
        setSessionExpired(false);
      } catch (error) {
        tokenStore.clear();
        throw error;
      }
    },
    [resetCache],
  );

  const signOut = useCallback(() => {
    const captured = { access: tokenStore.getAccess(), refresh: tokenStore.getRefresh() };
    endSession(false);
    // Sunucu çağrısının sonucu yerel çıkışı etkilemez (ör. bağlantı hatası).
    void logoutWithTokens(captured).catch(() => undefined);
  }, [endSession]);

  const expireSession = useCallback(() => endSession(true), [endSession]);

  const dismissSessionExpired = useCallback(() => {
    endSession(false);
  }, [endSession]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      isAuthenticated: status === 'authenticated' && user !== null,
      signIn,
      signOut,
      sessionExpired,
      expireSession,
      dismissSessionExpired,
    }),
    [user, status, signIn, signOut, sessionExpired, expireSession, dismissSessionExpired],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth, AuthProvider içinde kullanılmalıdır');
  return ctx;
}
