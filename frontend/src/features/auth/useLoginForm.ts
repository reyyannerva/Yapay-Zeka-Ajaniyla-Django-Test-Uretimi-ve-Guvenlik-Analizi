import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

// Backend (SimpleJWT) `username` + `password` bekler (H5-03 / #41). Kullanıcı adı e-posta biçiminde
// olabileceği için biçim doğrulanmaz, yalnızca zorunluluk denetlenir.
export const loginSchema = z.object({
  username: z.string().trim().min(1, 'Kullanıcı adı zorunludur.'),
  password: z.string().min(1, 'Parolanızı girin.'),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export function useLoginForm() {
  return useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  });
}
