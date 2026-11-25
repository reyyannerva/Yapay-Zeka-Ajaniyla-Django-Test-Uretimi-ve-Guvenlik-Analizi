import { useState } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { getMe, login } from '../../lib/api/auth';
import { isApiError } from '../../lib/api/client';
import { useAuth } from '../../lib/auth-context';
import { AuthShell } from './AuthShell';
import { useLoginForm } from './useLoginForm';
import type { LoginFormValues } from './useLoginForm';

type LoginFailure = 'invalid' | 'locked' | 'unknown';

const LOCK_MESSAGE =
  'Çok fazla başarısız giriş denemesi. Hesap geçici olarak kilitlendi; lütfen bir süre sonra tekrar deneyin.';
// Kilit yanıtında kalan süre alanı yoktur; yalnızca politika bilgisi gösterilir (geri sayım yok).
const LOCK_POLICY = '3 başarısız denemede hesap 15 dk kilitlenir.';

const ALERT_CLASSES = 'rounded-md border border-error bg-error-bg p-3 text-sm';

function readFrom(state: unknown): string {
  const from = (state as { from?: { pathname?: string } } | null)?.from?.pathname;
  return from && from !== '/login' ? from : '/dashboard';
}

export function Login() {
  const { isAuthenticated, signInMock } = useAuth();
  const location = useLocation();
  const [failure, setFailure] = useState<LoginFailure | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useLoginForm();

  if (isAuthenticated) {
    return <Navigate to={readFrom(location.state)} replace />;
  }

  async function onSubmit(values: LoginFormValues) {
    setFailure(null);
    try {
      // E-posta alanı mantıksal olarak `username`'e eşlenir (nihai eşleme #41).
      await login({ username: values.email, password: values.password });
      signInMock(await getMe());
    } catch (error) {
      if (isApiError(error) && error.status === 429) setFailure('locked');
      else if (isApiError(error) && error.status === 401) setFailure('invalid');
      else setFailure('unknown');
    }
  }

  return (
    <AuthShell title="Giriş yap" subtitle="Hesabınızla oturum açın.">
      <form noValidate onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        {failure === 'locked' ? (
          <div role="alert" className={ALERT_CLASSES}>
            <strong className="block font-semibold text-error">Hesap kilitlendi</strong>
            <p className="mt-1">
              {LOCK_MESSAGE} {LOCK_POLICY}
            </p>
          </div>
        ) : null}
        {failure === 'invalid' ? (
          <div role="alert" className={ALERT_CLASSES}>
            E-posta veya parola hatalı.
          </div>
        ) : null}
        {failure === 'unknown' ? (
          <div role="alert" className={ALERT_CLASSES}>
            Giriş yapılamadı. Lütfen daha sonra tekrar deneyin.
          </div>
        ) : null}
        <Input
          label="E-posta"
          type="text"
          autoComplete="username"
          error={errors.email?.message}
          {...register('email')}
        />
        <Input
          label="Parola"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <Button type="submit" block disabled={isSubmitting}>
          Giriş yap
        </Button>
        <Link to="/forgot-password" className="text-center text-sm text-accent hover:underline">
          Şifremi unuttum
        </Link>
      </form>
    </AuthShell>
  );
}
