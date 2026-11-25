import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';

import { StageStrip } from './StageStrip';

test('StageStrip son düğüm "Tamamlandı"dır, "Rapor" aşaması yoktur', () => {
  render(<StageStrip status="COMPLETED" progress={{ total: 34, percent: 100 }} />);
  expect(screen.getByText(/Tamamlandı/)).toBeInTheDocument();
  expect(screen.queryByText(/^Rapor$/)).not.toBeInTheDocument();
});

test('StageStrip percent null iken yüzde göstermez, "henüz veri yok" der', () => {
  render(<StageStrip status="QUEUED" progress={{ total: 0, percent: null }} />);
  expect(screen.queryByText('%0')).not.toBeInTheDocument();
  expect(screen.getByText(/henüz/i)).toBeInTheDocument();
});

test('StageStrip kanonik altı düğümü sırayla gösterir', () => {
  render(<StageStrip status="EXECUTING" progress={{ total: 10, percent: 40 }} />);
  const items = screen.getAllByRole('listitem').map((li) => li.textContent);
  expect(items).toEqual([
    expect.stringContaining('Kuyruk'),
    expect.stringContaining('Analiz'),
    expect.stringContaining('Üretim'),
    expect.stringContaining('Çalıştırma'),
    expect.stringContaining('Tarama'),
    expect.stringContaining('Tamamlandı'),
  ]);
  expect(screen.getByText('%40')).toBeInTheDocument();
});

test('StageStrip geçerli aşamayı aria-current ile işaretler', () => {
  render(<StageStrip status="SCANNING" progress={{ total: 10, percent: 90 }} />);
  const current = screen
    .getAllByRole('listitem')
    .filter((li) => li.getAttribute('aria-current') === 'step');
  expect(current).toHaveLength(1);
  expect(current[0]).toHaveTextContent('Tarama');
});

test('StageStrip FAILED ve CANCELLED durumunu ayrıca belirtir', () => {
  const { rerender } = render(<StageStrip status="FAILED" progress={{ total: 5, percent: 20 }} />);
  expect(screen.getByRole('status')).toHaveTextContent('Başarısız');
  rerender(<StageStrip status="CANCELLED" progress={{ total: 5, percent: 20 }} />);
  expect(screen.getByRole('status')).toHaveTextContent('İptal edildi');
});
