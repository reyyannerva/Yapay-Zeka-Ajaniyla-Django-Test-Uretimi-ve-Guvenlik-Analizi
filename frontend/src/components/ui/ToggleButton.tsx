import { Button } from './Button';
import type { ButtonProps } from './Button';

export interface ToggleButtonProps extends Omit<ButtonProps, 'variant' | 'aria-pressed'> {
  pressed: boolean;
}

/** Filtre düğmesi: ortak `Button` (ghost) üzerine kurulur; seçili durum vurgu rengiyle gösterilir. */
export function ToggleButton({ pressed, className = '', ...rest }: ToggleButtonProps) {
  return (
    <Button
      variant="ghost"
      aria-pressed={pressed}
      className={`${pressed ? '!border-accent !bg-accent-soft !text-accent' : ''} ${className}`}
      {...rest}
    />
  );
}
