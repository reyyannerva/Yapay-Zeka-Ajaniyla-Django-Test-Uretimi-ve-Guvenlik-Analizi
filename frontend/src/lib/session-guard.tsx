import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

import { useAuth } from './auth-context';
import { isApiError } from './api/client';

/**
 * Herhangi bir sorgu/mutasyon 401 ile başarısız olunca oturumu düşürür; ProtectedRoute
 * kullanıcıyı ekran 12'ye (/session-expired) yönlendirir. Giriş denemesi (react-query dışı) etkilenmez.
 */
export function SessionGuard() {
  const queryClient = useQueryClient();
  const { expireSession, isAuthenticated } = useAuth();

  useEffect(() => {
    // Yalnızca açık bir oturum varken 401 oturumu düşürür; bilinçli çıkıştan sonra gelen 401'ler
    // kullanıcıyı "oturum süresi doldu" ekranına göndermez.
    const onEvent = (error: unknown) => {
      if (isAuthenticated && isApiError(error) && error.status === 401) expireSession();
    };
    const unsubscribeQueries = queryClient.getQueryCache().subscribe((event) => {
      if (event.type === 'updated' && event.action.type === 'error') onEvent(event.action.error);
    });
    const unsubscribeMutations = queryClient.getMutationCache().subscribe((event) => {
      if (event.type === 'updated' && event.action.type === 'error') onEvent(event.action.error);
    });
    return () => {
      unsubscribeQueries();
      unsubscribeMutations();
    };
  }, [queryClient, expireSession, isAuthenticated]);

  return null;
}
