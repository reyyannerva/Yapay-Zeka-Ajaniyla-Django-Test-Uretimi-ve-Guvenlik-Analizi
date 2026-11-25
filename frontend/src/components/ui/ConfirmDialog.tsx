import { Button } from './Button';
import { Modal } from './Modal';

export interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  /** İşlem sürerken düğmeleri devre dışı bırakır. */
  busy?: boolean;
  /** Geri alınamaz eylem: onay düğmesi kırmızı (danger) olur. */
  destructive?: boolean;
  /** Eylem başarısız olursa diyalog içinde gösterilen hata mesajı. */
  error?: string;
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Onayla',
  cancelLabel = 'Vazgeç',
  onConfirm,
  onCancel,
  busy = false,
  destructive = false,
  error,
}: ConfirmDialogProps) {
  return (
    <Modal
      open={open}
      onClose={onCancel}
      title={title}
      footer={
        <>
          <Button variant="ghost" onClick={onCancel} disabled={busy}>
            {cancelLabel}
          </Button>
          <Button
            variant={destructive ? 'danger' : 'primary'}
            onClick={onConfirm}
            disabled={busy}
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      {description ? <p className="text-muted">{description}</p> : null}
      {error ? (
        <p role="alert" className="mt-3 rounded-md border border-error bg-error-bg p-3 text-fg">
          {error}
        </p>
      ) : null}
    </Modal>
  );
}
