import { TEST_STATUS_META } from '../../lib/analysis-status';
import type { TestTone } from '../../lib/analysis-status';
import type { TestExecutionStatus } from '../../types';

// Her test durumu ayrı bir ikon + kod + Türkçe etiketle gösterilir; renk tek başına anlam taşımaz.
const TONE_CLASSES: Record<TestTone, string> = {
  pass: 'bg-pass-bg text-pass border-pass',
  fail: 'bg-fail-bg text-fail border-fail',
  error: 'bg-error-bg text-error border-error',
  timeout: 'bg-timeout-bg text-timeout border-timeout',
  process: 'bg-process-bg text-process border-process',
  muted: 'bg-surface-2 text-muted border-border-strong',
};

function Glyph({ status }: { status: TestExecutionStatus }) {
  const common = {
    width: 12,
    height: 12,
    viewBox: '0 0 12 12',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.6,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
  };
  switch (status) {
    case 'PASS':
      return <svg {...common}><path d="M2.5 6.3l2.3 2.3 4.7-5" /></svg>;
    case 'FAIL':
      return <svg {...common}><path d="M3 3l6 6M9 3L3 9" /></svg>;
    case 'ERROR':
      return <svg {...common}><path d="M6 1.8L10.8 10H1.2z M6 5v2.2" /></svg>;
    case 'TIMEOUT':
      return <svg {...common}><circle cx="6" cy="6" r="4.6" /><path d="M6 3.6V6l1.7 1.2" /></svg>;
    case 'RUNNING':
      return <svg {...common} className="animate-spin motion-reduce:animate-none"><path d="M6 1.4a4.6 4.6 0 1 1-4.6 4.6" /></svg>;
    case 'PENDING':
      return <svg {...common}><circle cx="6" cy="6" r="4.2" strokeDasharray="2 2" /></svg>;
    default:
      return <svg {...common}><path d="M3 6h6" /></svg>;
  }
}

export interface TestStatusIndicatorProps {
  status: TestExecutionStatus;
}

export function TestStatusIndicator({ status }: TestStatusIndicatorProps) {
  const meta = TEST_STATUS_META[status] ?? { label: 'Bilinmeyen durum', tone: 'muted' as const };
  return (
    <span
      data-status={status}
      data-tone={meta.tone}
      title={meta.label}
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-medium ${TONE_CLASSES[meta.tone]}`}
    >
      <Glyph status={status} />
      {status}
      <span className="sr-only">{` (${meta.label})`}</span>
    </span>
  );
}
