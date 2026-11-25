import { render, screen } from '@testing-library/react';
import { useForm } from 'react-hook-form';
import userEvent from '@testing-library/user-event';
import { expect, test, vi } from 'vitest';

import { Input } from './Input';

test('error verilince hata metnini ve aria-invalid gösterir', () => {
  render(<Input label="E-posta" error="Geçerli bir e-posta girin" />);
  const input = screen.getByLabelText('E-posta');
  expect(input).toHaveAttribute('aria-invalid', 'true');
  expect(screen.getByText('Geçerli bir e-posta girin')).toBeInTheDocument();
  expect(input).toHaveAccessibleDescription('Geçerli bir e-posta girin');
});

test('error yokken aria-invalid işaretlenmez', () => {
  render(<Input label="E-posta" />);
  expect(screen.getByLabelText('E-posta')).not.toHaveAttribute('aria-invalid', 'true');
});

test('react-hook-form register ile (ref iletimi) çalışır', async () => {
  const onSubmit = vi.fn();
  function Form() {
    const { register, handleSubmit } = useForm<{ email: string }>();
    return (
      <form onSubmit={handleSubmit(onSubmit)}>
        <Input label="E-posta" {...register('email')} />
        <button type="submit">Gönder</button>
      </form>
    );
  }
  render(<Form />);
  await userEvent.type(screen.getByLabelText('E-posta'), 'a@b.test');
  await userEvent.click(screen.getByRole('button', { name: 'Gönder' }));
  expect(onSubmit).toHaveBeenCalledTimes(1);
  expect(onSubmit.mock.calls[0][0]).toEqual({ email: 'a@b.test' });
});
