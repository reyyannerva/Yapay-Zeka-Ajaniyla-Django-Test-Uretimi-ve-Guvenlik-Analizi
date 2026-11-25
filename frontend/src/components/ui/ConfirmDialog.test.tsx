import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';

import { ConfirmDialog } from './ConfirmDialog';

const noop = () => undefined;

test('destructive onay düğmesi danger varyantını kullanır', () => {
  render(
    <ConfirmDialog open destructive title="Sil" confirmLabel="Sil" onConfirm={noop} onCancel={noop} />,
  );
  expect(screen.getByRole('button', { name: 'Sil' })).toHaveClass('bg-error');
});

test('varsayılan onay düğmesi danger değildir', () => {
  render(<ConfirmDialog open title="Onay" onConfirm={noop} onCancel={noop} />);
  expect(screen.getByRole('button', { name: 'Onayla' })).not.toHaveClass('bg-error');
});

test('error verilirse uyarı olarak gösterilir', () => {
  render(
    <ConfirmDialog open title="Onay" error="Bir şey ters gitti." onConfirm={noop} onCancel={noop} />,
  );
  expect(screen.getByRole('alert')).toHaveTextContent('Bir şey ters gitti.');
});
