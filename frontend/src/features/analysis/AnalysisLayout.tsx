import { useQuery } from '@tanstack/react-query';
import { Link, NavLink, Outlet } from 'react-router-dom';

import { Card } from '../../components/ui/Card';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { Spinner } from '../../components/ui/Spinner';
import { errorMessage } from '../../lib/api/errors';
import { StageStrip } from '../../components/ui/StageStrip';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { listDemoProjects } from '../../lib/api/demo-analysis';
import { getProject } from '../../lib/api/projects';
import { METHOD_LABEL, PROVIDER_LABEL } from '../../lib/analysis-labels';
import { queryKeys } from '../../lib/queryKeys';
import { formatDate } from '../projects/ProjectValidationBadge';
import { DemoNotice } from './DemoNotice';
import { useAnalysisRun, useRunId } from './useAnalysisData';
import type { AnalysisOutletContext, AnalysisSource } from './useAnalysisData';

/** Kaynağa göre liste adresi: gerçek kayıtlar /analyses, DEMO prototip /demo/analyses. */
export function analysesBasePath(source: AnalysisSource): string {
  return source === 'api' ? '/analyses' : '/demo/analyses';
}

const SUMMARY_TAB = { to: 'summary', label: 'Özet' } as const;

export const ANALYSIS_TABS = [
  { to: 'endpoints', label: 'Kaynak kod analizi' },
  { to: 'tests', label: 'Üretilen testler' },
  { to: 'results', label: 'Test sonuçları' },
  { to: 'findings', label: 'Güvenlik bulguları' },
  { to: 'report', label: 'Rapor' },
] as const;

function Meta({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="text-sm font-medium text-fg">{children}</dd>
    </div>
  );
}

function NotFoundRun({ source }: { source: AnalysisSource }) {
  return (
    <EmptyState
      title="Analiz bulunamadı"
      description="Analiz silinmiş olabilir, adres hatalı olabilir ya da size ait olmayabilir."
      action={
        <Link to={analysesBasePath(source)} className="text-sm font-medium text-accent hover:underline">
          Analizlere dön
        </Link>
      }
    />
  );
}

export function AnalysisLayout({ source = 'api' }: { source?: AnalysisSource }) {
  const runId = useRunId();
  const run = useAnalysisRun(runId, source);
  const projectId = run.data?.project ?? 0;
  const project = useQuery({
    queryKey: queryKeys.projects.detail(projectId),
    queryFn: ({ signal }) => getProject(projectId, signal),
    enabled: source === 'api' && run.data !== undefined,
  });
  const demoProjects = useQuery({
    queryKey: queryKeys.demo.projects(),
    queryFn: listDemoProjects,
    enabled: source === 'demo',
  });

  const runError = run.error as { status?: number } | null;
  if (run.isError && runError && (runError.status === 0 || (runError.status ?? 0) >= 500)) {
    // Bağlantı/sunucu hatası "bulunamadı" ile karıştırılmaz.
    return <ErrorState title="Analiz alınamadı" description={errorMessage(run.error)} />;
  }
  if (runId === null || run.isError) return <NotFoundRun source={source} />;
  if (run.isLoading || !run.data) return <Spinner label="Analiz yükleniyor" />;

  const data = run.data;
  const projectName =
    source === 'api' ? project.data?.name : demoProjects.data?.find((p) => p.id === data.project)?.name;
  const projectLabel = projectName ?? `Proje ${data.project}`;
  const context: AnalysisOutletContext = { run: data, source };
  const tabs = source === 'api' ? [SUMMARY_TAB, ...ANALYSIS_TABS] : ANALYSIS_TABS;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-3">
        <nav aria-label="Konum" className="text-sm text-muted">
          <Link to={analysesBasePath(source)} className="text-accent hover:underline">
            {source === 'api' ? 'Analizler' : 'DEMO analizler'}
          </Link>
          {' / '}
          {source === 'api' ? (
            <Link to={`/projects/${data.project}`} className="hover:underline">
              {projectLabel}
            </Link>
          ) : (
            projectLabel
          )}
          {` / #${data.id}`}
        </nav>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="font-display text-2xl font-semibold text-fg">{`Analiz #${data.id}`}</h1>
          <StatusBadge status={data.status} />
        </div>
        {source === 'demo' ? <DemoNotice /> : null}
      </header>

      <Card className="flex flex-col gap-4">
        <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <Meta label="Proje">{projectLabel}</Meta>
          <Meta label="Yöntem">{METHOD_LABEL[data.method]}</Meta>
          <Meta label="LLM sağlayıcı">
            {data.llm_provider ? PROVIDER_LABEL[data.llm_provider] : data.method === 'RULE_BASED' ? 'Gerekmez' : 'Bilinmiyor'}
          </Meta>
          <Meta label="Fallback">{data.fallback_enabled ? 'Açık' : 'Kapalı'}</Meta>
          <Meta label="Başlangıç">{data.started_at ? formatDate(data.started_at) : 'Henüz başlamadı'}</Meta>
        </dl>
        <div className="border-t border-border pt-4">
          <p className="mb-2 text-xs font-medium text-muted">Analiz aşaması ve test ilerlemesi (backend özeti)</p>
          <StageStrip status={data.status} progress={data.progress} />
          {data.status === 'FAILED' && data.error_message ? (
            <p className="mt-3 text-sm text-error">{data.error_message}</p>
          ) : null}
        </div>
      </Card>

      <nav aria-label="Analiz bölümleri" className="-mb-2 overflow-x-auto border-b border-border">
        <ul className="flex min-w-max gap-1">
          {tabs.map((tab) => (
            <li key={tab.to}>
              <NavLink
                to={tab.to}
                className={({ isActive }) =>
                  `inline-block border-b-2 px-3 py-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent ${
                    isActive ? 'border-accent font-semibold text-accent' : 'border-transparent text-muted hover:text-fg'
                  }`
                }
              >
                {tab.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <Outlet context={context} />
    </div>
  );
}
