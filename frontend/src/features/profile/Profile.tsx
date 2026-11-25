import { useQuery } from '@tanstack/react-query';

import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { EmptyState } from '../../components/ui/EmptyState';
import { Input } from '../../components/ui/Input';
import { Spinner } from '../../components/ui/Spinner';
import { useToast } from '../../components/ui/Toast';
import { getMe } from '../../lib/api/auth';
import { queryKeys } from '../../lib/queryKeys';
import type { User } from '../../types';
import { PASSWORD_CHANGE_DEFAULTS, usePasswordChangeForm } from './usePasswordChangeForm';

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

function PasswordCard() {
  const toast = useToast();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = usePasswordChangeForm();

  // Mock: gerçek parola değiştirme çağrısı #41'de bağlanır; şimdilik yalnızca doğrulama + onay.
  async function onSubmit() {
    toast.show('Parolanız güncellendi (örnek veri: gerçek bir değişiklik yapılmadı).', 'success');
    reset(PASSWORD_CHANGE_DEFAULTS);
  }

  return (
    <Card>
      <form noValidate onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <h2 className="font-display text-lg font-semibold text-fg">Şifre değiştir</h2>
        <Input
          label="Mevcut parola"
          type="password"
          autoComplete="current-password"
          error={errors.current_password?.message}
          {...register('current_password')}
        />
        <Input
          label="Yeni parola"
          type="password"
          autoComplete="new-password"
          error={errors.new_password?.message}
          {...register('new_password')}
        />
        <Input
          label="Yeni parola (tekrar)"
          type="password"
          autoComplete="new-password"
          error={errors.confirm?.message}
          {...register('confirm')}
        />
        <div className="flex justify-end">
          <Button type="submit" disabled={isSubmitting}>
            Parolayı değiştir
          </Button>
        </div>
      </form>
    </Card>
  );
}

export function Profile() {
  const { data: user, isLoading, isError } = useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: getMe,
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
