import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { z } from 'zod';

import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { requestPasswordReset } from '../../lib/api/auth';
import { AuthShell } from './AuthShell';

const schema = z.object({
  email: z.string().trim().min(1, 'E-posta zorunludur.').email('Geçerli bir e-posta adresi girin.'),
});
type Values = z.infer<typeof schema>;

export function ForgotPassword() {
  const [sent, setSent] = useState(false);
  const [failed, setFailed] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { email: '' } });

  async function onSubmit(values: Values) {
    setFailed(false);
    try {
      await requestPasswordReset(values.email);
      setSent(true);
    } catch {
      setFailed(true);
    }
  }

  return (
    <AuthShell
      title="Şifremi unuttum"
      subtitle="E-posta adresinizi girin; sıfırlama bağlantısı gönderelim."
    >
      {sent ? (
        // Kayıtlı/kayıtsız adres için yanıt aynıdır; hesabın varlığı ifşa edilmez.
        <div className="flex flex-col gap-4">
          <div role="status" className="rounded-md border border-pass bg-pass-bg p-3 text-sm">
            Bu e-posta adresi kayıtlıysa şifre sıfırlama bağlantısı gönderildi. Gelen kutunuzu
            kontrol edin.
          </div>
          <Link to="/login" className="text-center text-sm text-accent hover:underline">
            Girişe dön
          </Link>
        </div>
      ) : (
        <form noValidate onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          {failed ? (
            <div
              role="alert"
              className="rounded-md border border-error bg-error-bg p-3 text-sm"
            >
              İstek gönderilemedi. Lütfen daha sonra tekrar deneyin.
            </div>
          ) : null}
          <Input
            label="E-posta"
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email')}
          />
          <Button type="submit" block disabled={isSubmitting}>
            Bağlantı gönder
          </Button>
          <Link to="/login" className="text-center text-sm text-accent hover:underline">
            Girişe dön
          </Link>
        </form>
      )}
    </AuthShell>
  );
}
