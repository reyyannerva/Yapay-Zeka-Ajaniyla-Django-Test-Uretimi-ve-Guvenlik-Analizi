import { useEffect, useState } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Spinner } from '../../components/ui/Spinner';
import { isApiError } from '../../lib/api/client';
import { useAuth } from '../../lib/auth-context';
import { AuthShell } from './AuthShell';
import { formatRemaining, lockInfoFrom } from './lockout';
import { useLoginForm } from './useLoginForm';
import type { LoginFormValues } from './useLoginForm';

type LoginFailure =
  | { kind: 'invalid' }
  | { kind: 'locked'; deadline: number | null }
  | { kind: 'throttled' }
  | { kind: 'network'; detail: string }
  | { kind: 'unknown' };

const LOCK_MESSAGE =
  'Çok fazla başarısız giriş denemesi. Hesap geçici olarak kilitlendi; lütfen bir süre sonra tekrar deneyin.';
const LOCK_POLICY = '3 başarısız denemede hesap 15 dk kilitlenir. Kilit kararı sunucu tarafından verilir.';

const ALERT_CLASSES = 'rounded-md border border-error bg-error-bg p-3 text-sm';

function readFrom(state: unknown): string {
  const from = (state as { from?: { pathname?: string } } | null)?.from?.pathname;
  return from && from !== '/login' ? from : '/dashboard';
}

/** Sunucunun bildirdiği kalan süreden türetilen gösterim amaçlı geri sayım. */
function LockCountdown({ deadline }: { deadline: number }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  const remaining = (deadline - now) / 1000;
  if (remaining <= 0) {
    return <p className="mt-1 font-medium">Kilit süresi doldu; tekrar giriş yapmayı deneyebilirsiniz.</p>;
  }
  return (
    <p className="mt-1" data-testid="lock-remaining">
      Kalan süre: <strong className="font-mono">{formatRemaining(remaining)}</strong> (sunucunun bildirdiği süreye göre)
    </p>
  );
}

export function Login() {
  const { isAuthenticated, status, signIn } = useAuth();
  const location = useLocation();
  const [failure, setFailure] = useState<LoginFailure | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useLoginForm();

  if (status === 'checking') {
    return (
      <AuthShell title="Giriş yapın">
        <Spinner label="Oturum doğrulanıyor" />
      </AuthShell>
    );
  }
  if (isAuthenticated) {
    return <Navigate to={readFrom(location.state)} replace />;
  }

  async function onSubmit(values: LoginFormValues) {
    setFailure(null);
    try {
      await signIn({ username: values.username, password: values.password });
    } catch (error) {
      if (!isApiError(error)) {
        setFailure({ kind: 'unknown' });
        return;
      }
      const lock = lockInfoFrom(error);
      if (lock) {
        setFailure({
          kind: 'locked',
          deadline: lock.retryAfterSeconds === null ? null : Date.now() + lock.retryAfterSeconds * 1000,
        });
      } else if (error.status === 429) setFailure({ kind: 'throttled' });
      else if (error.status === 401) setFailure({ kind: 'invalid' });
      else if (error.status === 0) setFailure({ kind: 'network', detail: String((error.body as { detail?: string }).detail) });
      else setFailure({ kind: 'unknown' });
    }
  }

  return (
    <AuthShell
      eyebrow="Oturum"
      title="Giriş yapın"
      subtitle="Analizlerinize devam etmek için hesabınızla giriş yapın."
    >
      <form noValidate onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        {failure?.kind === 'locked' ? (
          <div role="alert" className={ALERT_CLASSES}>
            <strong className="block font-semibold text-error">Hesap kilitlendi</strong>
            <p className="mt-1">
              {LOCK_MESSAGE} {LOCK_POLICY}
            </p>
            {failure.deadline !== null ? <LockCountdown deadline={failure.deadline} /> : null}
          </div>
        ) : null}
        {failure?.kind === 'throttled' ? (
          <div role="alert" className={ALERT_CLASSES}>
            Kısa sürede çok fazla giriş isteği gönderildi. Lütfen biraz bekleyip tekrar deneyin.
          </div>
        ) : null}
        {failure?.kind === 'invalid' ? (
          <div role="alert" className={ALERT_CLASSES}>
            Kullanıcı adı veya parola hatalı.
          </div>
        ) : null}
        {failure?.kind === 'network' ? (
          <div role="alert" className={ALERT_CLASSES}>
            {failure.detail}
          </div>
        ) : null}
        {failure?.kind === 'unknown' ? (
          <div role="alert" className={ALERT_CLASSES}>
            Giriş yapılamadı. Lütfen daha sonra tekrar deneyin.
          </div>
        ) : null}
        <Input
          label="Kullanıcı adı"
          type="text"
          autoComplete="username"
          error={errors.username?.message}
          {...register('username')}
        />
        <Input
          label="Parola"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <div className="flex items-center justify-end gap-3 text-sm">
          <Link to="/forgot-password" className="font-semibold text-accent hover:underline">
            Şifremi unuttum
          </Link>
        </div>
        <Button type="submit" block disabled={isSubmitting} aria-busy={isSubmitting}>
          {isSubmitting ? 'Giriş yapılıyor…' : 'Giriş yap'}
        </Button>
        <p className="border-t border-border pt-4 text-xs leading-relaxed text-muted">
          Hesabınız yoksa ekip yöneticinizden davet isteyin. Oturum bu tarayıcı sekmesine özeldir; sekme
          kapatıldığında sona erer.
        </p>
      </form>
    </AuthShell>
  );
}
