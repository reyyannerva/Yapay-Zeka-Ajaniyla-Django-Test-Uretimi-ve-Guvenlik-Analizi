import { render, screen, within } from '@testing-library/react';
import { expect, test } from 'vitest';

import { ExperimentResults } from './ExperimentResults';
import { experiment, formatRatio, targetTone } from './experimentData';

test('sayfa çevrimdışı deney olarak etiketlenir; DEMO veya canlı analiz gibi sunulmaz', () => {
  render(<ExperimentResults />);
  expect(screen.getByText('ÇEVRİMDIŞI DENEY')).toBeInTheDocument();
  expect(screen.getByText(/Canlı bir analiz kaydı veya DEMO verisi değildir/)).toBeInTheDocument();
  expect(screen.queryByText('DEMO')).not.toBeInTheDocument();
});

test('gerçek model kimliği ve kaynak özeti gösterilir', () => {
  render(<ExperimentResults />);
  expect(screen.getByText(experiment.model)).toBeInTheDocument();
  expect(screen.getByText(new RegExp(experiment.sourceSha256.slice(0, 12)))).toBeInTheDocument();
});

test('iki katman ve üç yöntem tabloda yer alır', () => {
  render(<ExperimentResults />);
  const tables = screen.getAllByRole('table');
  expect(tables).toHaveLength(2);
  for (const t of tables) {
    for (const label of ['Kural tabanlı (H3-04)', 'Groq LLM (H3-05)', 'Hibrit (H5-05)']) {
      expect(within(t).getByText(label)).toBeInTheDocument();
    }
  }
});

test('Katman A F1 "Ölçülemedi" olarak kalır ve çubuk olarak (0 gibi) çizilmez', () => {
  const a = experiment.layers.find((l) => l.key === 'A')!;
  expect(a.positives).toBe(0);
  expect(a.methods.every((m) => m.f1.value === null && m.f1.display === 'Ölçülemedi')).toBe(true);
  render(<ExperimentResults />);
  expect(screen.getAllByTestId('not-measurable')).toHaveLength(3);
  expect(screen.queryByRole('img', { name: /F1/ })).not.toBeInTheDocument();
});

test('ilk geçiş pay/payda snapshot ile aynı biçimde gösterilir', () => {
  render(<ExperimentResults />);
  const b = experiment.layers.find((l) => l.key === 'B')!;
  const m = b.methods[0];
  expect(screen.getAllByText(`${m.firstPassExecutable.count}/${m.firstPassExecutable.of} · ${formatRatio(m.firstPassExecutable)}`).length).toBeGreaterThan(0);
});

test('hedef durumları yalnızca "Karşılandı" ise başarı tonunda', () => {
  expect(targetTone('Karşılandı')).toBe('pass');
  expect(targetTone('Karşılanmadı')).toBe('fail');
  expect(targetTone('Ölçülemedi')).toBe('muted');
  expect(targetTone('Karşılaştırılamadı')).toBe('muted');
});

test('snapshot içeriği H5-05 gerçek sonuçlarıyla tutarlı (Katman B: 3 kusur, 5 metot)', () => {
  const b = experiment.layers.find((l) => l.key === 'B')!;
  expect(Object.values(b.httpMethods).every((n) => n > 0)).toBe(true);
  expect(Object.keys(b.httpMethods).sort()).toEqual(['DELETE', 'GET', 'PATCH', 'POST', 'PUT']);
  expect(b.positives).toBe(3);
  expect(b.llmStatus).toBe('GENERATED');
});
