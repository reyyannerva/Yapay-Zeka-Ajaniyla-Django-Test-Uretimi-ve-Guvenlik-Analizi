import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { deleteProject } from '../../lib/api/projects';
import { queryKeys } from '../../lib/queryKeys';
import type { Project } from '../../types';
import { translateProjectError } from './useProjectForm';

export interface DeleteConfirmProps {
  open: boolean;
  project: Pick<Project, 'id' | 'name'>;
  onClose: () => void;
  /** Silme başarılı olunca çağrılır (çağıran yönlendirme/bildirim yapar). */
  onDeleted: () => void;
}

/** Proje silme onayı (ekran 30). Aktif analizli proje için sunucu 409'u diyalog içinde gösterilir. */
export function DeleteConfirm({ open, project, onClose, onDeleted }: DeleteConfirmProps) {
  const queryClient = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | undefined>();

  function handleClose() {
    setError(undefined);
    onClose();
  }

  async function handleConfirm() {
    setBusy(true);
    setError(undefined);
    try {
      await deleteProject(project.id);
      await queryClient.invalidateQueries({ queryKey: queryKeys.projects.all() });
      queryClient.removeQueries({ queryKey: queryKeys.projects.detail(project.id) });
      onDeleted();
    } catch (failure) {
      setError(translateProjectError(failure).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <ConfirmDialog
      open={open}
      destructive
      busy={busy}
      title="Projeyi sil"
      description={`"${project.name}" projesi ve yüklenen arşivi kalıcı olarak silinecek. Bu işlem geri alınamaz.`}
      confirmLabel="Sil"
      cancelLabel="Vazgeç"
      error={error}
      onConfirm={() => void handleConfirm()}
      onCancel={handleClose}
    />
  );
}
