import { hashKey, useQueryClient, type QueryClient, type QueryKey } from '@tanstack/react-query';
import { useState } from 'react';

import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { deleteProject } from '../../lib/api/projects';
import { queryKeys } from '../../lib/queryKeys';
import type { PaginatedProjectList, Project } from '../../types';
import { translateProjectError } from './useProjectForm';

export interface DeleteConfirmProps {
  open: boolean;
  project: Pick<Project, 'id' | 'name'>;
  onClose: () => void;
  /** Silme başarılı olunca çağrılır (çağıran yönlendirme/bildirim yapar). */
  onDeleted: () => void;
}

/** Sorguyu, ekrandaki gözlemcisi (mount'lu bileşen) kalkar kalkmaz önbellekten siler. */
function removeWhenUnobserved(queryClient: QueryClient, queryKey: QueryKey) {
  const cache = queryClient.getQueryCache();
  const query = cache.find({ queryKey, exact: true });
  if (!query) return;
  if (query.getObserversCount() === 0) {
    cache.remove(query);
    return;
  }
  const unsubscribe = cache.subscribe((event) => {
    if (event.type === 'observerRemoved' && event.query === query && query.getObserversCount() === 0) {
      unsubscribe();
      cache.remove(query);
    }
  });
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
    const detailKey = queryKeys.projects.detail(project.id);
    setBusy(true);
    setError(undefined);
    try {
      await deleteProject(project.id);
      // Sunucu silmeyi onayladı (204): önbellekteki listelerden kayıt hemen çıkarılır; aksi hâlde liste
      // yeniden çekilene kadar silinmiş proje bir an görünürdü. Hata durumunda hiçbir kayıt kaldırılmaz.
      queryClient.setQueriesData<PaginatedProjectList>({ queryKey: ['projects', 'list'] }, (old) =>
        old ? { ...old, count: Math.max(0, old.count - 1), results: old.results.filter((p) => p.id !== project.id) } : old,
      );
      // Silinen projenin detayı ekrandayken yeniden çekilmemeli ve önbellekten de ekran bırakılmadan
      // atılmamalı (ikisi de "Yükleniyor"/"Proje bulunamadı" flaşına yol açar). Sıra: önce
      // yönlendir, detayı yeniden çekmeden listeyi geçersiz kıl, detayı gözlemcisi kalkınca sil.
      onDeleted();
      removeWhenUnobserved(queryClient, detailKey);
      // CASCADE: projeye bağlı analiz ve referans kayıtları da sunucuda silindi (H5-03 / #41).
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: queryKeys.projects.all(),
          predicate: (query) => query.queryHash !== hashKey(detailKey),
        }),
        queryClient.invalidateQueries({ queryKey: queryKeys.analysisRuns.all() }),
        queryClient.invalidateQueries({ queryKey: queryKeys.referenceRequirements.all() }),
      ]);
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
      description={`"${project.name}" projesi, yüklenen arşivi ve projeye bağlı analiz ile referans gereksinim kayıtları kalıcı olarak silinecek. Bu işlem geri alınamaz.`}
      confirmLabel="Sil"
      cancelLabel="Vazgeç"
      error={error}
      onConfirm={() => void handleConfirm()}
      onCancel={handleClose}
    />
  );
}
