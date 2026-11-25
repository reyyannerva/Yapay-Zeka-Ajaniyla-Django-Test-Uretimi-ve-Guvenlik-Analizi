import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

// Form etiketi "E-posta"dır (Figma); değer mantıksal olarak API'deki `username` alanına eşlenir (nihai eşleme #41).
// Bu yüzden biçim (e-posta formatı) doğrulanmaz, yalnızca zorunluluk denetlenir.
export const loginSchema = z.object({
  email: z.string().trim().min(1, 'E-posta zorunludur.'),
  password: z.string().min(1, 'Parolanızı girin.'),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export function useLoginForm() {
  return useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });
}
