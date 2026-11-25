import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { useAuth } from '../../lib/auth-context';
import { Spinner } from '../ui/Spinner';

/**
 * Kimliksiz kullanıcıyı /login'e (oturum süresi dolduysa /session-expired'a) yönlendirir; girişten sonra
 * dönülecek konum `state.from`'da tutulur. Saklanan oturum doğrulanırken korumalı içerik gösterilmez.
 */
export function ProtectedRoute() {
  const { isAuthenticated, sessionExpired, status } = useAuth();
  const location = useLocation();

  if (status === 'checking') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-app-bg">
        <Spinner label="Oturum doğrulanıyor" />
      </div>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to={sessionExpired ? '/session-expired' : '/login'} replace state={{ from: location }} />;
  }
  return <Outlet />;
}
