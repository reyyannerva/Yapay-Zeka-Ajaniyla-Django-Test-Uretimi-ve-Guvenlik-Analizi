import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { useAuth } from '../../lib/auth-context';

/** Kimliksiz kullanıcıyı /login'e (oturum süresi dolduysa /session-expired'a) yönlendirir; girişten sonra dönülecek konum `state.from`'da tutulur. */
export function ProtectedRoute() {
  const { isAuthenticated, sessionExpired } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to={sessionExpired ? '/session-expired' : '/login'} replace state={{ from: location }} />;
  }
  return <Outlet />;
}
