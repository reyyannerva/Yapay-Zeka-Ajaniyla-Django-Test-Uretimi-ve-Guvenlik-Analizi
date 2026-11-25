import { useQuery } from '@tanstack/react-query';

import { getAnalysisRun, listAnalysisRuns } from '../../lib/api/analysis-runs';
import { listProjects } from '../../lib/api/projects';
import { queryKeys } from '../../lib/queryKeys';
import type { AnalysisRun, AnalysisRunDetail, AnalysisRunStatus, Project } from '../../types';

/** Çalışmakta olan (kuyruk ve uç durumlar hariç) aşamalar. */
const IN_PROGRESS: readonly AnalysisRunStatus[] = [
  'ANALYZING',
  'GENERATING',
  'VALIDATING',
  'EXECUTING',
  'SCANNING',
];

export function isInProgress(status: AnalysisRunStatus): boolean {
  return IN_PROGRESS.includes(status);
}

export interface OverviewMetrics {
  projectCount: number;
  runCount: number;
  inProgressCount: number;
  completedCount: number;
}

export interface OverviewData {
  isLoading: boolean;
  isError: boolean;
  metrics: OverviewMetrics | null;
  /** En yeni önce. */
  recentRuns: AnalysisRun[];
  /** Aşama şeridi için ayrıntılı (progress içeren) devam eden analizler. */
  activeRuns: AnalysisRunDetail[];
  /** Proje kimliği → ad (kullanıcının projeleri). */
  projectNames: Record<number, string>;
}

export function useOverviewData(): OverviewData {
  const projects = useQuery({
    queryKey: queryKeys.projects.list({ page: 1, page_size: 100 }),
    queryFn: ({ signal }) => listProjects({ page: 1, page_size: 100 }, signal),
  });
  const runs = useQuery({
    queryKey: queryKeys.analysisRuns.list(),
    queryFn: ({ signal }) => listAnalysisRuns(signal),
  });

  const runList = runs.data;
  const activeIds = (runList ?? []).filter((r) => isInProgress(r.status)).map((r) => r.id);

  // Liste yanıtında progress yoktur; devam edenlerin ayrıntısı ayrıca alınır.
  const active = useQuery({
    queryKey: [...queryKeys.analysisRuns.list(), 'active', activeIds] as const,
    queryFn: ({ signal }) => Promise.all(activeIds.map((id) => getAnalysisRun(id, signal))),
    enabled: runList !== undefined,
  });

  const isLoading = projects.isLoading || runs.isLoading || active.isLoading;
  const isError = projects.isError || runs.isError || active.isError;

  if (!projects.data || !runList) {
    return { isLoading, isError, metrics: null, recentRuns: [], activeRuns: [], projectNames: {} };
  }

  const recentRuns = [...runList].sort((a, b) => b.created_at.localeCompare(a.created_at));
  const metrics: OverviewMetrics = {
    projectCount: projects.data.count,
    runCount: runList.length,
    inProgressCount: activeIds.length,
    completedCount: runList.filter((r) => r.status === 'COMPLETED').length,
  };
  const projectNames = Object.fromEntries(projects.data.results.map((p: Project) => [p.id, p.name]));

  return { isLoading, isError, metrics, recentRuns, activeRuns: active.data ?? [], projectNames };
}
