import type { ReactNode } from 'react';

export interface ErrorStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

/** Hata durumu: boş veriden (EmptyState) ayrıdır; teknik ayrıntı veya stack trace göstermez. */
export function ErrorState({ title, description, action }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-3 rounded-lg border border-error bg-error-bg px-6 py-8 text-center"
    >
      <h2 className="font-display text-lg font-semibold text-fg">{title}</h2>
      {description ? <p className="max-w-md text-sm text-muted">{description}</p> : null}
      {action ? <div className="mt-1">{action}</div> : null}
    </div>
  );
}
