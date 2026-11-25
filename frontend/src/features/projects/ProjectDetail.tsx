import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { EmptyState } from '../../components/ui/EmptyState';
import { Spinner } from '../../components/ui/Spinner';
import { useToast } from '../../components/ui/Toast';
import type { Project } from '../../types';
import { DeleteConfirm } from './DeleteConfirm';
import { NEW_PROJECT_LINK_CLASSES } from './ProjectList';
import { ProjectValidationBadge, formatDate } from './ProjectValidationBadge';
import { isApiError } from '../../lib/api/client';
import { Unauthorized } from '../status/Unauthorized';
import { ErrorState } from '../../components/ui/ErrorState';
import { errorMessage } from '../../lib/api/errors';
import { ReferenceRequirementsCard } from '../requirements/ReferenceRequirementsCard';
import { StartAnalysisCard } from './StartAnalysisCard';
import { useRouteProject } from './useProject';

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} KiB`;
  return `${(bytes / (1024 * 1024)).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} MiB`;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="text-sm text-fg">{children}</dd>
    </div>
  );
}

function ValidationReport({ project }: { project: Project }) {
  const report = project.validation_report;
  if (!report) {
    return <p className="text-sm text-muted">Doğrulama raporu henüz oluşmadı.</p>;
  }
  const rejected = report.rejected_entries ?? [];
  const warnings = report.warnings ?? [];
  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      <Field label="manage.py">{report.manage_py_found ? 'Bulundu' : 'Bulunamadı'}</Field>
      <Field label="Django REST framework">
        {report.drf_detected === undefined ? '—' : report.drf_detected ? 'Algılandı' : 'Algılanmadı'}
      </Field>
      <Field label="Django uygulamaları">
        {report.django_apps && report.django_apps.length > 0 ? report.django_apps.join(', ') : '—'}
      </Field>
      <Field label="Uyarılar">{warnings.length > 0 ? warnings.join('; ') : 'Yok'}</Field>
      {rejected.length > 0 ? (
        <div className="sm:col-span-2">
          <dt className="text-xs text-muted">Reddedilen girdiler</dt>
          <dd>
            <ul className="mt-1 flex flex-col gap-1 text-sm">
              {rejected.map((entry) => (
                <li key={`${entry.path}:${entry.reason}`}>
                  <code className="font-mono text-xs">{entry.path}</code>{' '}
                  <span className="text-error">({entry.reason})</span>
                </li>
              ))}
            </ul>
          </dd>
        </div>
      ) : null}
    </dl>
  );
}

export function ProjectDetail() {
  const { id, isValidId, data: project, isLoading, isError, error } = useRouteProject();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const navigate = useNavigate();
  const toast = useToast();

  // Gerçek 403: başkasının kaynağı → ekran 13. 404 (silinmiş/olmayan) aşağıda "Proje bulunamadı" kalır.
  if (isError && isApiError(error) && error.status === 403) return <Unauthorized />;
  // Bağlantı/sunucu hatası "bulunamadı" ile karıştırılmaz.
  if (isError && isApiError(error) && (error.status === 0 || error.status >= 500)) {
    return <ErrorState title="Proje alınamadı" description={errorMessage(error)} />;
  }
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
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-col gap-2">
          <Link to="/projects" className="text-sm text-accent hover:underline">
            ← Projeler
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-display text-2xl font-semibold text-fg">{project.name}</h1>
            <ProjectValidationBadge status={project.validation_status} />
          </div>
          {project.description ? <p className="text-sm text-muted">{project.description}</p> : null}
        </div>
        <div className="flex gap-2">
          <Link
            to={`/projects/${id}/edit`}
            className="inline-flex items-center justify-center rounded-md border border-border-strong px-4 py-2 text-sm font-medium text-fg hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            Düzenle
          </Link>
          <Button variant="danger" onClick={() => setConfirmOpen(true)}>
            Projeyi sil
          </Button>
        </div>
      </header>

      <Card className="flex flex-col gap-4">
        <h2 className="font-display text-lg font-semibold">Arşiv</h2>
        {project.archive ? (
          <dl className="grid gap-3 sm:grid-cols-2">
            <Field label="Dosya adı">{project.archive.original_name}</Field>
            <Field label="Boyut">{formatSize(project.archive.size_bytes)}</Field>
            <Field label="Yüklenme">{formatDate(project.archive.uploaded_at)}</Field>
            <Field label="SHA-256">
              <code className="break-all font-mono text-xs">{project.archive.sha256}</code>
            </Field>
          </dl>
        ) : (
          <p className="text-sm text-muted">Bu proje bir arşivden oluşturulmadı.</p>
        )}
      </Card>

      <Card className="flex flex-col gap-4">
        <h2 className="font-display text-lg font-semibold">Doğrulama raporu</h2>
        <ValidationReport project={project} />
      </Card>

      <StartAnalysisCard project={project} />

      <ReferenceRequirementsCard projectId={project.id} />

      <DeleteConfirm
        open={confirmOpen}
        project={project}
        onClose={() => setConfirmOpen(false)}
        onDeleted={() => {
          setConfirmOpen(false);
          toast.show('Proje silindi.', 'success');
          navigate('/projects');
        }}
      />
    </div>
  );
}
