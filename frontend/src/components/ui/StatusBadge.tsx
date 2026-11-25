import {
  FINDING_META,
  SEVERITY_LABEL,
  STATUS_META,
  TEST_STATUS_META,
  findingTone,
} from '../../lib/analysis-status';
import type { FindingTone, RunTone, TestTone } from '../../lib/analysis-status';
import type {
  AnalysisRunStatus,
  SecurityFindingClassification,
  Severity,
  TestExecutionStatus,
} from '../../types';

type Tone = RunTone | TestTone | FindingTone;

// Yalnızca tema token sınıfları kullanılır; renk tek başına anlam taşımaz (etiket her zaman yazılır).
const TONE_CLASSES: Record<Tone, string> = {
  pass: 'bg-pass-bg text-pass border-pass',
  fail: 'bg-fail-bg text-fail border-fail',
  error: 'bg-error-bg text-error border-error',
  timeout: 'bg-timeout-bg text-timeout border-timeout',
  process: 'bg-process-bg text-process border-process',
  muted: 'bg-surface-2 text-muted border-border-strong',
};

interface BadgeProps {
  tone: Tone;
  children: string;
  className?: string;
}

function Badge({ tone, children, className = '' }: BadgeProps) {
  return (
    <span
      data-tone={tone}
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${TONE_CLASSES[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: AnalysisRunStatus }) {
  const meta = STATUS_META[status];
  return <Badge tone={meta.tone}>{meta.label}</Badge>;
}

export function TestStatusBadge({ status }: { status: TestExecutionStatus }) {
  const meta = TEST_STATUS_META[status];
  return <Badge tone={meta.tone}>{meta.label}</Badge>;
}

export interface FindingBadgeProps {
  classification: SecurityFindingClassification;
  severity?: Severity;
}

export function FindingBadge({ classification, severity }: FindingBadgeProps) {
  const meta = FINDING_META[classification];
  const tone = findingTone(classification, severity);
  return (
    <span className="inline-flex items-center gap-1.5">
      <Badge tone={tone}>{meta.label}</Badge>
      {severity ? <span className="text-xs text-muted">{SEVERITY_LABEL[severity]}</span> : null}
    </span>
  );
}
