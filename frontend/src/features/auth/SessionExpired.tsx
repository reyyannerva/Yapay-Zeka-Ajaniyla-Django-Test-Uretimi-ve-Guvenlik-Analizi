import { useNavigate } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { useAuth } from '../../lib/auth-context';
import { AuthShell } from './AuthShell';

/** Ekran 12: oturum süresi doldu. `expireSession()` (ör. 401 yanıtı → SessionGuard) ProtectedRoute üzerinden buraya yönlendirir. */
export function SessionExpired() {
  const { dismissSessionExpired } = useAuth();
  const navigate = useNavigate();

  function goToLogin() {
    // Oturum hâlâ açık görünüyorsa temizle; aksi hâlde /login kimlikli kullanıcıyı geri yönlendirirdi.
    dismissSessionExpired();
    navigate('/login', { replace: true });
  }

  return (
    <AuthShell title="Oturum süreniz doldu" subtitle="Güvenliğiniz için oturumunuz sonlandırıldı.">
      <div className="flex flex-col gap-4">
        <p className="text-sm text-muted">Devam etmek için lütfen yeniden giriş yapın.</p>
        <Button block onClick={goToLogin}>
          Yeniden giriş yap
        </Button>
      </div>
    </AuthShell>
  );
}
