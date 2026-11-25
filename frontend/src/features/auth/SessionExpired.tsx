import { useNavigate } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { useAuth } from '../../lib/auth-context';
import { AuthShell } from './AuthShell';

/** Ekran 12: oturum süresi doldu. Mock'ta `/session-expired` adresinden elle tetiklenir (gerçek tetikleme #41). */
export function SessionExpired() {
  const { expireSession } = useAuth();
  const navigate = useNavigate();

  function goToLogin() {
    // Oturum hâlâ açık görünüyorsa temizle; aksi hâlde /login kimlikli kullanıcıyı geri yönlendirirdi.
    expireSession();
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
