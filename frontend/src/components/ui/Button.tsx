import type { ButtonHTMLAttributes } from 'react';

type ButtonVariant = 'primary' | 'ghost' | 'danger';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  /** Kapsayıcının tam genişliğini kaplar. */
  block?: boolean;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: 'bg-accent text-accent-fg border border-transparent hover:opacity-90',
  ghost: 'bg-transparent text-fg border border-border-strong hover:bg-surface-2',
  // Yıkıcı eylemler (ör. silme onayı): hata tokenlarıyla kırmızı.
  danger: 'bg-error text-error-fg border border-transparent hover:opacity-90',
};

export function Button({
  variant = 'primary',
  block = false,
  type = 'button',
  className = '',
  ...rest
}: ButtonProps) {
  const classes = [
    'inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium',
    'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent',
    'disabled:cursor-not-allowed disabled:opacity-50',
    VARIANT_CLASSES[variant],
    block ? 'w-full' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');
  return <button type={type} className={classes} {...rest} />;
}
