import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { EmptyState } from '../../components/ui/EmptyState';
import { Input } from '../../components/ui/Input';
import { Spinner } from '../../components/ui/Spinner';
import { useToast } from '../../components/ui/Toast';
import { updateProject } from '../../lib/api/projects';
import { queryKeys } from '../../lib/queryKeys';
import type { Project } from '../../types';
import { NEW_PROJECT_LINK_CLASSES } from './ProjectList';
import { useRouteProject } from './useProject';
import { translateProjectError, useProjectEditForm } from './useProjectForm';
import type { ProjectEditValues } from './useProjectForm';

function EditForm({ project }: { project: Project }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const toast = useToast();
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useProjectEditForm({ name: project.name, description: project.description });

  async function onSubmit(values: ProjectEditValues) {
    setFormError(null);
    try {
      await updateProject(project.id, { name: values.name, description: values.description });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.projects.all() }),
        queryClient.invalidateQueries({ queryKey: queryKeys.analysisRuns.all() }),
      ]);
      toast.show('Proje güncellendi.', 'success');
      navigate(`/projects/${project.id}`);
    } catch (error) {
      const { message, fieldErrors } = translateProjectError(error);
      if (fieldErrors?.name) setError('name', { message: fieldErrors.name });
      if (fieldErrors?.description) setError('description', { message: fieldErrors.description });
      if (!fieldErrors?.name && !fieldErrors?.description) setFormError(message);
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
      <p className="text-xs text-muted">
        Yüklenen arşiv değiştirilemez; farklı bir arşiv için yeni proje oluşturun.
      </p>
      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={() => navigate(`/projects/${project.id}`)} disabled={isSubmitting}>
          Vazgeç
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          Kaydet
        </Button>
      </div>
    </form>
  );
}

export function ProjectEdit() {
  const { isValidId, data: project, isLoading, isError } = useRouteProject();

  if (!isValidId || isError) {
    return (
      <EmptyState
        title="Proje bulunamadı"
        description="Proje silinmiş olabilir ya da size ait değildir."
        action={
          <Link to="/projects" className={NEW_PROJECT_LINK_CLASSES}>
            Projelere dön
          </Link>
        }
      />
    );
  }
  if (isLoading || !project) return <Spinner />;

  return (
    <div className="flex max-w-xl flex-col gap-6">
      <h1 className="font-display text-2xl font-semibold text-fg">Projeyi düzenle</h1>
      <Card>
        <EditForm project={project} />
      </Card>
    </div>
  );
}
