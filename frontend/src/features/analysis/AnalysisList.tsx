import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';

import { DataTable } from '../../components/ui/DataTable';
import type { DataTableColumn } from '../../components/ui/DataTable';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { Spinner } from '../../components/ui/Spinner';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { listAnalysisRuns } from '../../lib/api/analysis-runs';
import { listDemoAnalysisRuns, listDemoProjects } from '../../lib/api/demo-analysis';
import { errorMessage } from '../../lib/api/errors';
import { listProjects } from '../../lib/api/projects';
import { METHOD_LABEL, PROVIDER_LABEL } from '../../lib/analysis-labels';
import { queryKeys } from '../../lib/queryKeys';
import type { AnalysisRun } from '../../types';
import { formatDate } from '../projects/ProjectValidationBadge';
import { analysesBasePath } from './AnalysisLayout';
import { DemoNotice } from './DemoNotice';
import type { AnalysisSource } from './useAnalysisData';

export function AnalysisList({ source = 'api' }: { source?: AnalysisSource }) {
  const [params] = useSearchParams();
  const projectFilter = Number(params.get('project'));
  const base = analysesBasePath(source);
  const runs = useQuery({
    queryKey: source === 'api' ? queryKeys.analysisRuns.list() : queryKeys.demo.analysisRuns.list(),
    queryFn: ({ signal }) => (source === 'api' ? listAnalysisRuns(signal) : listDemoAnalysisRuns()),
  });
  const projects = useQuery({
    queryKey: source === 'api' ? [...queryKeys.projects.all(), 'names'] : queryKeys.demo.projects(),
    queryFn: ({ signal }) =>
      source === 'api'
        ? listProjects({ page: 1, page_size: 100 }, signal).then((page) => page.results)
        : listDemoProjects(),
  });

  const projectName = (id: number) => projects.data?.find((p) => p.id === id)?.name ?? `Proje ${id}`;

  const columns: readonly DataTableColumn<AnalysisRun>[] = [
    {
      key: 'id',
      header: 'Analiz',
      cell: (run) => (
        <Link to={`${base}/${run.id}`} className="font-mono font-medium text-accent hover:underline">
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
        <h1 className="font-display text-2xl font-semibold text-fg">
          {source === 'api' ? 'Analizler' : 'DEMO analiz örnekleri'}
        </h1>
        {source === 'api' ? (
          <p className="text-sm text-muted">
            {'Hesabınıza ait gerçek analiz kayıtları. Sonuç ekranlarının örnek görünümü için '}
            <Link to="/demo/analyses" className="text-accent hover:underline">
              DEMO analiz örneklerine
            </Link>
            {' bakabilirsiniz.'}
          </p>
        ) : (
          <>
            <DemoNotice />
            <Link to="/analyses" className="self-start text-sm text-accent hover:underline">
              Gerçek analizlere dön
            </Link>
          </>
        )}
        {projectFilter > 0 ? (
          <p className="text-sm text-muted">
            {`${projectName(projectFilter)} projesinin analizleri gösteriliyor. `}
            <Link to={base} className="text-accent hover:underline">
              Tüm analizler
            </Link>
          </p>
        ) : null}
      </header>
      {runs.isLoading ? (
        <Spinner />
      ) : runs.isError ? (
        <ErrorState title="Analizler alınamadı" description={errorMessage(runs.error)} />
      ) : (
        <DataTable
          columns={columns}
          rows={filtered}
          rowKey={(run) => run.id}
          emptyState={
            <EmptyState
              title="Analiz bulunamadı"
              description={
                source === 'api'
                  ? 'Bir proje detayından analiz başlattığınızda kayıt burada listelenir.'
                  : 'DEMO kaydı yok.'
              }
            />
          }
        />
      )}
    </div>
  );
}
