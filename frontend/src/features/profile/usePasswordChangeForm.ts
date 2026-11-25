import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

/** Mock doğrulama: en az uzunluk (gerçek parola politikası backend'de, #41'de eşlenir). */
export const MIN_PASSWORD_LENGTH = 8;

export const passwordChangeSchema = z
  .object({
    current_password: z.string().min(1, 'Mevcut parola zorunludur.'),
    new_password: z
      .string()
      .min(1, 'Yeni parola zorunludur.')
      .min(MIN_PASSWORD_LENGTH, `Yeni parola en az ${MIN_PASSWORD_LENGTH} karakter olmalıdır.`)
      .refine((v) => !/^\d+$/.test(v), 'Yeni parola yalnızca rakamlardan oluşamaz.'),
    confirm: z.string().min(1, 'Parola tekrarı zorunludur.'),
  })
  .refine((v) => v.new_password === v.confirm, {
    path: ['confirm'],
    message: 'Parolalar eşleşmiyor.',
  })
  .refine((v) => !v.new_password || v.new_password !== v.current_password, {
    path: ['new_password'],
    message: 'Yeni parola mevcut paroladan farklı olmalıdır.',
  });

export type PasswordChangeValues = z.infer<typeof passwordChangeSchema>;

export const PASSWORD_CHANGE_DEFAULTS: PasswordChangeValues = {
  current_password: '',
  new_password: '',
  confirm: '',
};

export function usePasswordChangeForm() {
  return useForm<PasswordChangeValues>({
    resolver: zodResolver(passwordChangeSchema),
    defaultValues: PASSWORD_CHANGE_DEFAULTS,
  });
}
