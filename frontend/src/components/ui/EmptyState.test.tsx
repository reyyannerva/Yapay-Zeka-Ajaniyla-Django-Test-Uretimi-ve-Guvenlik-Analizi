import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';

import { Button } from './Button';
import { EmptyState } from './EmptyState';

test('başlık, açıklama ve aksiyonu render eder', () => {
  render(
    <EmptyState
      title="Henüz proje yok"
      description="İlk projenizi oluşturun."
      action={<Button>Proje oluştur</Button>}
    />,
  );
  expect(screen.getByText('Henüz proje yok')).toBeInTheDocument();
  expect(screen.getByText('İlk projenizi oluşturun.')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Proje oluştur' })).toBeInTheDocument();
});

test('aksiyon verilmezse yalnızca başlığı render eder', () => {
  render(<EmptyState title="Boş" />);
  expect(screen.getByText('Boş')).toBeInTheDocument();
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
});
