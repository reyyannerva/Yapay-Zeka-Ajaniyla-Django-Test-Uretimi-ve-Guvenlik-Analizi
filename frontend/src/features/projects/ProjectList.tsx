import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { DataTable } from '../../components/ui/DataTable';
import type { DataTableColumn } from '../../components/ui/DataTable';
import { EmptyState } from '../../components/ui/EmptyState';
import { Spinner } from '../../components/ui/Spinner';
import { listProjects } from '../../lib/api/projects';
import { queryKeys } from '../../lib/queryKeys';
import type { Project } from '../../types';
import { ProjectValidationBadge, formatDate } from './ProjectValidationBadge';

const PAGE_SIZE = 20;

export const NEW_PROJECT_LINK_CLASSES =
  'inline-flex items-center justify-center rounded-md border border-transparent bg-accent px-4 py-2 text-sm font-medium text-accent-fg hover:opacity-90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent';

const COLUMNS: readonly DataTableColumn<Project>[] = [
  {
    key: 'name',
    header: 'Proje',
    cell: (project) => (
      <Link
        to={`/projects/${project.id}`}
        className="font-medium text-accent hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
      >
        {project.name}
      </Link>
    ),
  },
  {
    key: 'validation',
    header: 'Doğrulama',
    cell: (project) => <ProjectValidationBadge status={project.validation_status} />,
  },
  { key: 'runs', header: 'Analiz sayısı', cell: (project) => project.analysis_run_count },
  { key: 'created', header: 'Oluşturulma', cell: (project) => formatDate(project.created_at) },
];

export function ProjectList() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.projects.list({ page, page_size: PAGE_SIZE }),
    queryFn: ({ signal }) => listProjects({ page, page_size: PAGE_SIZE }, signal),
  });

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-2xl font-semibold text-fg">Projeler</h1>
        <Link to="/projects/new" className={NEW_PROJECT_LINK_CLASSES}>
          Yeni proje
        </Link>
      </header>

      {isLoading ? (
        <Spinner />
      ) : isError || !data ? (
        <EmptyState title="Projeler alınamadı" description="Lütfen daha sonra tekrar deneyin." />
      ) : (
        <>
          <DataTable
            columns={COLUMNS}
            rows={data.results}
            rowKey={(project) => project.id}
            emptyState={
              <EmptyState
                title="Henüz proje yok"
                description="Bir Django arşivi yükleyerek başlayın."
                action={
                  <Link to="/projects/new" className={NEW_PROJECT_LINK_CLASSES}>
                    Yeni proje
                  </Link>
                }
              />
            }
          />
          {data.previous || data.next ? (
            <nav aria-label="Sayfalama" className="flex items-center justify-end gap-2">
              <Button variant="ghost" disabled={!data.previous} onClick={() => setPage(page - 1)}>
                Önceki
              </Button>
              <span className="text-sm text-muted">Sayfa {page}</span>
              <Button variant="ghost" disabled={!data.next} onClick={() => setPage(page + 1)}>
                Sonraki
              </Button>
            </nav>
          ) : null}
        </>
      )}
    </div>
  );
}
