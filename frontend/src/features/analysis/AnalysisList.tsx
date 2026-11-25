import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';

import { DataTable } from '../../components/ui/DataTable';
import type { DataTableColumn } from '../../components/ui/DataTable';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { Spinner } from '../../components/ui/Spinner';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { listAnalysisRuns } from '../../lib/api/analysis-runs';
import { listProjects } from '../../lib/api/projects';
import { METHOD_LABEL, PROVIDER_LABEL } from '../../lib/analysis-labels';
import { queryKeys } from '../../lib/queryKeys';
import type { AnalysisRun } from '../../types';
import { formatDate } from '../projects/ProjectValidationBadge';
import { DemoNotice } from './DemoNotice';

export function AnalysisList() {
  const [params] = useSearchParams();
  const projectFilter = Number(params.get('project'));
  const runs = useQuery({ queryKey: queryKeys.analysisRuns.list(), queryFn: listAnalysisRuns });
  const projects = useQuery({
    queryKey: queryKeys.projects.list({ page: 1, page_size: 100 }),
    queryFn: () => listProjects({ page: 1, page_size: 100 }),
  });

  const projectName = (id: number) =>
    projects.data?.results.find((p) => p.id === id)?.name ?? `Proje ${id}`;

  const columns: readonly DataTableColumn<AnalysisRun>[] = [
    {
      key: 'id',
      header: 'Analiz',
      cell: (run) => (
        <Link to={`/analyses/${run.id}`} className="font-mono font-medium text-accent hover:underline">
          {`#${run.id}`}
        </Link>
      ),
    },
    { key: 'project', header: 'Proje', cell: (run) => projectName(run.project) },
    { key: 'method', header: 'Yöntem', cell: (run) => METHOD_LABEL[run.method] },
    { key: 'status', header: 'Durum', cell: (run) => <StatusBadge status={run.status} /> },
    {
      key: 'provider',
      header: 'LLM sağlayıcı',
      cell: (run) => (run.llm_provider ? PROVIDER_LABEL[run.llm_provider] : '—'),
    },
    { key: 'created', header: 'Oluşturulma', cell: (run) => formatDate(run.created_at) },
  ];

  const filtered = (runs.data ?? [])
    .filter((r) => !Number.isInteger(projectFilter) || projectFilter <= 0 || r.project === projectFilter)
    .sort((a, b) => b.created_at.localeCompare(a.created_at));

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <h1 className="font-display text-2xl font-semibold text-fg">Analizler</h1>
        <DemoNotice />
        {projectFilter > 0 ? (
          <p className="text-sm text-muted">
            {`${projectName(projectFilter)} projesinin analizleri gösteriliyor. `}
            <Link to="/analyses" className="text-accent hover:underline">
              Tüm analizler
            </Link>
          </p>
        ) : null}
      </header>
      {runs.isLoading ? (
        <Spinner />
      ) : runs.isError ? (
        <ErrorState title="Analizler alınamadı" description="Lütfen daha sonra tekrar deneyin." />
      ) : (
        <DataTable
          columns={columns}
          rows={filtered}
          rowKey={(run) => run.id}
          emptyState={
            <EmptyState
              title="Analiz bulunamadı"
              description="Bir proje için analiz başlatıldığında burada listelenir."
            />
          }
        />
      )}
    </div>
  );
}
