import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';

import { MetricCard } from './MetricCard';

test('MetricCard etiket, değer ve ipucunu gösterir', () => {
  render(<MetricCard label="Toplam test" value={34} hint="son çalıştırma" />);
  expect(screen.getByText('Toplam test')).toBeInTheDocument();
  expect(screen.getByText('34')).toBeInTheDocument();
  expect(screen.getByText('son çalıştırma')).toBeInTheDocument();
});

test('MetricCard düz ince kenarlık kullanır, sol renkli şerit yoktur', () => {
  const { container } = render(<MetricCard label="Hata" value={2} alert />);
  const root = container.firstElementChild as HTMLElement;
  expect(root.className).toMatch(/\bborder\b/);
  expect(root.className).not.toMatch(/border-l/);
});
