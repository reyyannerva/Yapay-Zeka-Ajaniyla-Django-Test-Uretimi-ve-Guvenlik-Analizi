import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { Card } from '../../components/ui/Card';
import { EmptyState } from '../../components/ui/EmptyState';
import { Input } from '../../components/ui/Input';
import { Spinner } from '../../components/ui/Spinner';
import { getMe } from '../../lib/api/auth';
import { queryKeys } from '../../lib/queryKeys';
import type { User } from '../../types';

function AccountCard({ user }: { user: User }) {
  return (
    <Card className="flex flex-col gap-4">
      <h2 className="font-display text-lg font-semibold text-fg">Hesap bilgisi</h2>
      <Input label="Kullanıcı adı" value={user.username} readOnly />
      <Input label="E-posta" value={user.email} readOnly />
      <p className="text-xs text-muted">
        Ad ve e-posta bilgilerinizi yönetici günceller; bu ekrandan değiştirilemez.
      </p>
    </Card>
  );
}

/**
 * Backend'de oturum içi parola değiştirme uç noktası yoktur (H5-03 / #41 denetimi). Sahte başarı
 * göstermemek için kullanıcı gerçek API'ye bağlı e-posta ile sıfırlama akışına yönlendirilir.
 */
function PasswordCard() {
  return (
    <Card className="flex flex-col gap-3">
      <h2 className="font-display text-lg font-semibold text-fg">Şifre değiştir</h2>
      <p className="text-sm text-muted">
        Parolanızı e-posta adresinize gönderilen sıfırlama bağlantısıyla değiştirebilirsiniz. Bağlantı sınırlı
        süre geçerlidir ve yalnızca bir kez kullanılabilir.
      </p>
      <Link to="/forgot-password" className="self-start text-sm font-medium text-accent hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent">
        Sıfırlama bağlantısı iste
      </Link>
    </Card>
  );
}

export function Profile() {
  const { data: user, isLoading, isError } = useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: ({ signal }) => getMe(signal),
  });

  return (
    <div className="flex max-w-xl flex-col gap-6">
      <h1 className="font-display text-2xl font-semibold text-fg">Profil</h1>
      {isLoading ? (
        <Spinner />
      ) : isError || !user ? (
        <EmptyState title="Profil alınamadı" description="Lütfen daha sonra tekrar deneyin." />
      ) : (
        <>
          <AccountCard user={user} />
          <PasswordCard />
        </>
      )}
    </div>
  );
}
