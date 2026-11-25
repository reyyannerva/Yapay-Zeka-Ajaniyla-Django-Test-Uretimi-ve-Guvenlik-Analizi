import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test, vi } from 'vitest';

import { ConfirmDialog } from './ConfirmDialog';
import { Modal } from './Modal';

test('Modal kapalıyken hiçbir şey çizmez', () => {
  render(
    <Modal open={false} onClose={() => {}} title="Başlık">
      İçerik
    </Modal>,
  );
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

test('Modal erişilebilir diyalog olarak açılır ve odak içeri taşınır', () => {
  render(
    <Modal open onClose={() => {}} title="Başlık">
      <button type="button">Tamam</button>
    </Modal>,
  );
  const dialog = screen.getByRole('dialog', { name: 'Başlık' });
  expect(dialog).toHaveAttribute('aria-modal', 'true');
  expect(dialog).toContainElement(document.activeElement as HTMLElement);
});

test('Modal Escape ile kapanır', async () => {
  const onClose = vi.fn();
  render(
    <Modal open onClose={onClose} title="Başlık">
      İçerik
    </Modal>,
  );
  await userEvent.keyboard('{Escape}');
  expect(onClose).toHaveBeenCalledTimes(1);
});

test('Modal Tab ile odağı diyalog içinde tutar', async () => {
  render(
    <Modal open onClose={() => {}} title="Başlık">
      <button type="button">Bir</button>
      <button type="button">İki</button>
    </Modal>,
  );
  const dialog = screen.getByRole('dialog');
  for (let i = 0; i < 6; i += 1) {
    await userEvent.tab();
    expect(dialog).toContainElement(document.activeElement as HTMLElement);
  }
});

test('Modal kapanınca odak önceki öğeye döner', () => {
  function Harness({ open }: { open: boolean }) {
    return (
      <>
        <button type="button">Aç</button>
        <Modal open={open} onClose={() => {}} title="Başlık">
          İçerik
        </Modal>
      </>
    );
  }
  const { rerender } = render(<Harness open={false} />);
  const trigger = screen.getByRole('button', { name: 'Aç' });
  trigger.focus();
  rerender(<Harness open />);
  expect(trigger).not.toHaveFocus();
  rerender(<Harness open={false} />);
  expect(trigger).toHaveFocus();
});

test('ConfirmDialog onay ve vazgeç geri çağrılarını tetikler', async () => {
  const onConfirm = vi.fn();
  const onCancel = vi.fn();
  render(
    <ConfirmDialog
      open
      title="Silinsin mi?"
      description="Bu işlem geri alınamaz."
      confirmLabel="Sil"
      onConfirm={onConfirm}
      onCancel={onCancel}
    />,
  );
  expect(screen.getByText('Bu işlem geri alınamaz.')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'Sil' }));
  expect(onConfirm).toHaveBeenCalledTimes(1);
  await userEvent.click(screen.getByRole('button', { name: 'Vazgeç' }));
  expect(onCancel).toHaveBeenCalledTimes(1);
});
