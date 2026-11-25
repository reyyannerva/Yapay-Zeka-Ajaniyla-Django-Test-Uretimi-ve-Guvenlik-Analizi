import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test, vi } from 'vitest';

import { ToastProvider, useToast } from './Toast';

function Trigger() {
  const { show } = useToast();
  return (
    <button type="button" onClick={() => show('Kaydedildi', 'success')}>
      Tetikle
    </button>
  );
}

test('useToast ile bildirim gösterilir ve kapatılabilir', async () => {
  render(
    <ToastProvider>
      <Trigger />
    </ToastProvider>,
  );
  await userEvent.click(screen.getByRole('button', { name: 'Tetikle' }));
  expect(screen.getByRole('status')).toHaveTextContent('Kaydedildi');
  await userEvent.click(screen.getByRole('button', { name: 'Bildirimi kapat' }));
  expect(screen.queryByText('Kaydedildi')).not.toBeInTheDocument();
});

test('ToastProvider dışında useToast hata verir', () => {
  function Bad() {
    useToast();
    return null;
  }
  // React beklenen render hatasını console.error'a yazar; test çıktısını temiz tutmak için bastırılır.
  const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  expect(() => render(<Bad />)).toThrow(/ToastProvider/);
  errorSpy.mockRestore();
});
