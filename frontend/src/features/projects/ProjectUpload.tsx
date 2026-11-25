import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import type { ChangeEvent } from 'react';

import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { createProject } from '../../lib/api/projects';
import { queryKeys } from '../../lib/queryKeys';
import type { Project } from '../../types';
import { translateProjectError, useProjectForm } from './useProjectForm';
import type { ProjectUploadValues } from './useProjectForm';

export interface ProjectUploadProps {
  /** Proje oluşturulunca çağrılır; çağıran yönlendirme/bildirim/sihirbaz adımını yönetir. */
  onUploaded?: (project: Project) => void;
  /** Verilirse "Vazgeç" düğmesi gösterilir. */
  onCancel?: () => void;
  submitLabel?: string;
}

/**
 * Bağımsız, yeniden kullanılabilir proje yükleme formu. Kendi başına `/projects/new`'de çalışır;
 * "Yeni analiz" sihirbazı (#40) adım 1'de `onUploaded` ile aynı bileşeni kullanır.
 * Üst sarmalayıcı olarak yalnızca QueryClientProvider gerekir.
 */
export function ProjectUpload({
  onUploaded,
  onCancel,
  submitLabel = 'Projeyi yükle',
}: ProjectUploadProps) {
  const queryClient = useQueryClient();
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setValue,
    resetField,
    setError,
    formState: { errors, isSubmitting },
  } = useProjectForm();

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFormError(null);
    const file = event.target.files?.[0];
    if (file) setValue('archive', file, { shouldDirty: true, shouldValidate: true });
    else resetField('archive');
  }

  async function onSubmit(values: ProjectUploadValues) {
    setFormError(null);
    try {
      const project = await createProject({
        name: values.name,
        description: values.description,
        archive: values.archive,
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.projects.all() });
      onUploaded?.(project);
    } catch (error) {
      // Sunucu reddi (400/413/415...) formu çökertmez; alana veya forma anlaşılır mesaj yazılır.
      const { message, fieldErrors } = translateProjectError(error);
      if (fieldErrors?.name) setError('name', { message: fieldErrors.name });
      if (fieldErrors?.description) setError('description', { message: fieldErrors.description });
      if (fieldErrors?.archive) setError('archive', { message: fieldErrors.archive });
      if (!fieldErrors || Object.keys(fieldErrors).length === 0) setFormError(message);
    }
  }

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      {formError ? (
        <div role="alert" className="rounded-md border border-error bg-error-bg p-3 text-sm">
          {formError}
        </div>
      ) : null}
      <Input label="Proje adı" autoComplete="off" error={errors.name?.message} {...register('name')} />
      <Input
        label="Açıklama (isteğe bağlı)"
        autoComplete="off"
        error={errors.description?.message}
        {...register('description')}
      />
      <div className="flex flex-col gap-1">
        <Input
          label="Proje arşivi"
          type="file"
          accept=".zip,application/zip,application/x-zip-compressed"
          error={errors.archive?.message}
          onChange={onFileChange}
        />
        <p className="text-xs text-muted">
          Tek bir ZIP arşivi seçin (üst sınır 50 MiB).
        </p>
      </div>
      {isSubmitting ? (
        <p role="status" className="text-sm text-muted">
          Arşiv sunucuya gönderiliyor ve güvenlik denetiminden geçiriliyor; büyük arşivlerde bu biraz sürebilir.
        </p>
      ) : null}
      <div className="flex justify-end gap-2">
        {onCancel ? (
          <Button variant="ghost" onClick={onCancel} disabled={isSubmitting}>
            Vazgeç
          </Button>
        ) : null}
        <Button type="submit" disabled={isSubmitting} aria-busy={isSubmitting}>
          {isSubmitting ? 'Yükleniyor…' : submitLabel}
        </Button>
      </div>
    </form>
  );
}
