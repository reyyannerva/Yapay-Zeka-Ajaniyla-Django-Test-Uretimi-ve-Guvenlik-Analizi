import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test, vi } from 'vitest';

import { Button } from './Button';

test('tıklanınca onClick çağrılır', async () => {
  const onClick = vi.fn();
  render(<Button onClick={onClick}>Kaydet</Button>);
  await userEvent.click(screen.getByRole('button', { name: 'Kaydet' }));
  expect(onClick).toHaveBeenCalledTimes(1);
});

test('disabled iken onClick çağrılmaz', async () => {
  const onClick = vi.fn();
  render(
    <Button onClick={onClick} disabled>
      Kaydet
    </Button>,
  );
  const button = screen.getByRole('button', { name: 'Kaydet' });
  expect(button).toBeDisabled();
  await userEvent.click(button);
  expect(onClick).not.toHaveBeenCalled();
});
