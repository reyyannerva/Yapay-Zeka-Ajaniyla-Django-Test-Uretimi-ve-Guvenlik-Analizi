import type { ReactNode } from 'react';

export interface MetricCardProps {
  label: string;
  value: ReactNode;
  hint?: string;
  /** Değeri dikkat çekici (hata) renginde gösterir; kenarlık yine düz ve ince kalır. */
  alert?: boolean;
}

export function MetricCard({ label, value, hint, alert = false }: MetricCardProps) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border bg-surface p-4">
      <span className="text-xs font-medium text-muted">{label}</span>
      <span
        className={`font-display text-2xl font-semibold ${alert ? 'text-error' : 'text-fg'}`}
      >
        {value}
      </span>
      {hint ? <span className="text-xs text-muted">{hint}</span> : null}
    </div>
  );
}
