export interface SpinnerProps {
  /** Ekran okuyucular için erişilebilir ad. */
  label?: string;
}

export function Spinner({ label = 'Yükleniyor' }: SpinnerProps) {
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm text-muted">
      <svg
        className="h-5 w-5 animate-spin text-accent"
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" className="opacity-25" />
        <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      </svg>
      <span className="sr-only">{label}</span>
    </span>
  );
}
