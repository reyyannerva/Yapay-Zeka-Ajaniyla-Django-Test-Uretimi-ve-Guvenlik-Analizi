import type { HTMLAttributes } from 'react';

export function Card({ className = '', ...rest }: HTMLAttributes<HTMLDivElement>) {
  const classes = ['rounded-lg border border-border bg-surface p-5 text-fg', className]
    .filter(Boolean)
    .join(' ');
  return <div className={classes} {...rest} />;
}
