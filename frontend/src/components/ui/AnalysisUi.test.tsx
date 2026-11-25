import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';

import type { TestExecutionStatus } from '../../types';
import { CodeBlock } from './CodeBlock';
import { HttpMethodBadge } from './HttpMethodBadge';
import { TestStatusIndicator } from './TestStatusIndicator';

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const STATUSES: TestExecutionStatus[] = ['PENDING', 'RUNNING', 'PASS', 'FAIL', 'ERROR', 'TIMEOUT', 'STOPPED', 'NOT_RUN'];

test.each(STATUSES)('TestStatusIndicator %s durumunu kod + Türkçe etiketle gösterir', (status) => {
  const { container } = render(<TestStatusIndicator status={status} />);
  const el = container.querySelector(`[data-status="${status}"]`);
  expect(el).not.toBeNull();
  expect(el).toHaveTextContent(status);
  expect(el?.querySelector('.sr-only')?.textContent).toMatch(/\(.+\)/);
});

test('ERROR ve TIMEOUT ayrı tonlarda, FAIL başarı tonu almaz', () => {
  render(
    <>
      <TestStatusIndicator status="ERROR" />
      <TestStatusIndicator status="TIMEOUT" />
      <TestStatusIndicator status="FAIL" />
    </>,
  );
  const tone = (s: string) => document.querySelector(`[data-status="${s}"]`)?.getAttribute('data-tone');
  expect(tone('ERROR')).not.toBe(tone('TIMEOUT'));
  expect(tone('FAIL')).not.toBe('pass');
});

test('HttpMethodBadge metodu metin olarak gösterir', () => {
  render(<HttpMethodBadge method="DELETE" />);
  expect(screen.getByText('DELETE')).toHaveAttribute('data-method', 'DELETE');
});

test('CodeBlock güvenilmeyen içeriği düz metin olarak gösterir', () => {
  const payload = '<img src=x onerror="alert(1)"><script>alert(2)</script>';
  const { container } = render(<CodeBlock code={payload} label="Çıktı" />);
  expect(container.querySelector('img')).toBeNull();
  expect(container.querySelector('script')).toBeNull();
  expect(screen.getByLabelText('Çıktı')).toHaveTextContent(payload);
});

test('CodeBlock kopyalar, durumu bildirir ve süre sonunda sıfırlar', async () => {
  vi.useFakeTimers();
  const writeText = vi.fn().mockResolvedValue(undefined);
  vi.stubGlobal('navigator', { clipboard: { writeText } });
  render(<CodeBlock code="def test_x(): pass" label="Kod" copyable />);
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Kod kopyala' }));
  });
  expect(writeText).toHaveBeenCalledWith('def test_x(): pass');
  expect(screen.getByRole('status')).toHaveTextContent('Kopyalandı');
  act(() => {
    vi.advanceTimersByTime(2100);
  });
  expect(screen.getByRole('status')).toHaveTextContent('');
});

test('CodeBlock pano erişimi yoksa hata durumunu gösterir', async () => {
  vi.stubGlobal('navigator', {});
  render(<CodeBlock code="x" label="Kod" copyable />);
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Kod kopyala' }));
  });
  expect(screen.getByRole('status')).toHaveTextContent('Kopyalanamadı');
});
