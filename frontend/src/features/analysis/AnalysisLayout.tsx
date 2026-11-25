import { useQuery } from '@tanstack/react-query';
import { Link, NavLink, Outlet } from 'react-router-dom';

import { Card } from '../../components/ui/Card';
import { EmptyState } from '../../components/ui/EmptyState';
import { Spinner } from '../../components/ui/Spinner';
import { StageStrip } from '../../components/ui/StageStrip';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { getProject } from '../../lib/api/projects';
import { METHOD_LABEL, PROVIDER_LABEL } from '../../lib/analysis-labels';
import { queryKeys } from '../../lib/queryKeys';
import { formatDate } from '../projects/ProjectValidationBadge';
import { DemoNotice } from './DemoNotice';
import { useAnalysisRun, useRunId } from './useAnalysisData';
import type { AnalysisOutletContext } from './useAnalysisData';

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

function NotFoundRun() {
  return (
    <EmptyState
      title="Analiz bulunamadı"
      description="Analiz silinmiş olabilir, adres hatalı olabilir ya da size ait olmayabilir."
      action={
        <Link to="/analyses" className="text-sm font-medium text-accent hover:underline">
          Analizlere dön
        </Link>
      }
    />
  );
}

export function AnalysisLayout() {
  const runId = useRunId();
  const run = useAnalysisRun(runId);
  const project = useQuery({
    queryKey: queryKeys.projects.detail(run.data?.project ?? 0),
    queryFn: () => getProject(run.data?.project ?? 0),
    enabled: run.data !== undefined,
  });

  if (runId === null || run.isError) return <NotFoundRun />;
  if (run.isLoading || !run.data) return <Spinner label="Analiz yükleniyor" />;

  const data = run.data;
  const projectLabel = project.data?.name ?? `Proje ${data.project}`;
  const context: AnalysisOutletContext = { run: data };

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-3">
        <nav aria-label="Konum" className="text-sm text-muted">
          <Link to="/analyses" className="text-accent hover:underline">
            Analizler
          </Link>
          {' / '}
          <Link to={`/projects/${data.project}`} className="hover:underline">
            {projectLabel}
          </Link>
          {` / #${data.id}`}
        </nav>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="font-display text-2xl font-semibold text-fg">{`Analiz #${data.id}`}</h1>
          <StatusBadge status={data.status} />
        </div>
        <DemoNotice />
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
          {ANALYSIS_TABS.map((tab) => (
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
