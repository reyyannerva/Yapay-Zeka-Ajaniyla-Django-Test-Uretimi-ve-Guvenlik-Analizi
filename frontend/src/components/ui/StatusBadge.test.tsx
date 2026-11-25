import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';

import { FINDING_META, STATUS_META, TEST_STATUS_META } from '../../lib/analysis-status';
import { FindingBadge, StatusBadge, TestStatusBadge } from './StatusBadge';

test('StatusBadge 9 durumun tümünü eşler', () => {
  (
    [
      'QUEUED',
      'ANALYZING',
      'GENERATING',
      'VALIDATING',
      'EXECUTING',
      'SCANNING',
      'COMPLETED',
      'FAILED',
      'CANCELLED',
    ] as const
  ).forEach((s) => {
    const { unmount } = render(<StatusBadge status={s} />);
    expect(screen.getByText(STATUS_META[s].label)).toBeInTheDocument();
    unmount();
  });
});

test('AnalysisRun tonları: aktif süreç teal, tamamlandı yeşil, başarısız kırmızı', () => {
  expect(STATUS_META.QUEUED.tone).toBe('muted');
  expect(STATUS_META.CANCELLED.tone).toBe('muted');
  expect(STATUS_META.ANALYZING.tone).toBe('process');
  expect(STATUS_META.SCANNING.tone).toBe('process');
  expect(STATUS_META.COMPLETED.tone).toBe('pass');
  expect(STATUS_META.FAILED.tone).toBe('error');
});

test("TestStatusBadge ERROR ile TIMEOUT'u farklı tonda gösterir", () => {
  expect(TEST_STATUS_META.ERROR.tone).not.toBe(TEST_STATUS_META.TIMEOUT.tone);
  render(
    <>
      <TestStatusBadge status="ERROR" />
      <TestStatusBadge status="TIMEOUT" />
    </>,
  );
  expect(screen.getByText(TEST_STATUS_META.ERROR.label)).toBeInTheDocument();
  expect(screen.getByText(TEST_STATUS_META.TIMEOUT.label)).toBeInTheDocument();
});

test('TestExecution tonları: PASS yeşil, FAIL amber, ERROR kırmızı, RUNNING teal', () => {
  expect(TEST_STATUS_META.PASS.tone).toBe('pass');
  expect(TEST_STATUS_META.FAIL.tone).toBe('fail');
  expect(TEST_STATUS_META.ERROR.tone).toBe('error');
  expect(TEST_STATUS_META.RUNNING.tone).toBe('process');
  expect(TEST_STATUS_META.PENDING.tone).toBe('muted');
  expect(TEST_STATUS_META.NOT_RUN.tone).toBe('muted');
  expect(TEST_STATUS_META.STOPPED.tone).toBe('muted');
});

test('FindingBadge VERIFIED başarı/yeşil tonu kullanmaz', () => {
  expect(FINDING_META.VERIFIED.tone).not.toBe('pass');
  render(<FindingBadge classification="VERIFIED" severity="HIGH" />);
  expect(screen.getByText(/doğrulan/i)).toBeInTheDocument();
});

test('FindingBadge: POSSIBLE amber, UNCERTAIN nötr', () => {
  expect(FINDING_META.POSSIBLE.tone).toBe('fail');
  expect(FINDING_META.UNCERTAIN.tone).toBe('muted');
});
