import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { z } from 'zod';

import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useToast } from '../../components/ui/Toast';
import { confirmPasswordReset } from '../../lib/api/auth';
import { isApiError } from '../../lib/api/client';
import { AuthShell } from './AuthShell';

const schema = z
  .object({
    new_password: z.string().min(1, 'Yeni parola zorunludur.'),
    confirm: z.string().min(1, 'Parola tekrarı zorunludur.'),
  })
  .refine((v) => v.new_password === v.confirm, {
    path: ['confirm'],
    message: 'Parolalar eşleşmiyor.',
  });
type Values = z.infer<typeof schema>;

const INVALID_LINK = 'Bağlantı geçersiz, süresi dolmuş veya daha önce kullanılmış.';
const ALERT_CLASSES = 'rounded-md border border-error bg-error-bg p-3 text-sm';

function firstMessage(body: unknown, field: string): string | undefined {
  const value = (body as Record<string, unknown> | null)?.[field];
  return Array.isArray(value) && typeof value[0] === 'string' ? value[0] : undefined;
}

export function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();
  // Bağlantıdaki uid/token bir kez okunur ve adres çubuğundan/geçmişten silinir (H5-03 / #41):
  // token tarayıcı geçmişinde, ekran görüntülerinde veya Referer başlığında kalmaz.
  const [link] = useState(() => ({ uid: params.get('uid'), token: params.get('token') }));
  const { uid, token } = link;
  const hasQuery = params.has('uid') || params.has('token');
  useEffect(() => {
    if (hasQuery) navigate('/reset-password', { replace: true });
  }, [hasQuery, navigate]);
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { new_password: '', confirm: '' },
  });

  if (!uid || !token) {
    return (
      <AuthShell title="Şifre sıfırla">
        <div className="flex flex-col gap-4">
          <div role="alert" className={ALERT_CLASSES}>
            {INVALID_LINK}
          </div>
          <Link to="/forgot-password" className="text-center text-sm text-accent hover:underline">
            Yeni bağlantı iste
          </Link>
        </div>
      </AuthShell>
    );
  }

  async function onSubmit(values: Values) {
    setFormError(null);
    try {
      await confirmPasswordReset({
        uid: uid as string,
        token: token as string,
        new_password: values.new_password,
      });
      toast.show('Parolanız güncellendi. Yeni parolanızla giriş yapabilirsiniz.', 'success');
      navigate('/login', { replace: true });
    } catch (error) {
      if (isApiError(error) && error.status === 400) {
        const weak = firstMessage(error.body, 'new_password');
        if (weak) {
          setError('new_password', { message: weak });
          return;
        }
        setFormError(firstMessage(error.body, 'token') ?? INVALID_LINK);
        return;
      }
      setFormError('Parola güncellenemedi. Lütfen daha sonra tekrar deneyin.');
    }
  }

  return (
    <AuthShell title="Şifre sıfırla" subtitle="Hesabınız için yeni bir parola belirleyin.">
      <form noValidate onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        {formError ? (
          <div role="alert" className={ALERT_CLASSES}>
            {formError}
          </div>
        ) : null}
        <Input
          label="Yeni parola"
          type="password"
          autoComplete="new-password"
          error={errors.new_password?.message}
          {...register('new_password')}
        />
        <Input
          label="Parola (tekrar)"
          type="password"
          autoComplete="new-password"
          error={errors.confirm?.message}
          {...register('confirm')}
        />
        <Button type="submit" block disabled={isSubmitting}>
          Parolayı güncelle
        </Button>
        <Link to="/login" className="text-center text-sm text-accent hover:underline">
          Girişe dön
        </Link>
      </form>
    </AuthShell>
  );
}
