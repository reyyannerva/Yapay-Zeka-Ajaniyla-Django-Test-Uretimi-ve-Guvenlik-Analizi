import { useQuery } from '@tanstack/react-query';

import { getAnalysisRun, listAnalysisRuns } from '../../lib/api/analysis-runs';
import { listProjects } from '../../lib/api/projects';
import { queryKeys } from '../../lib/queryKeys';
import type {
  AnalysisRun,
  AnalysisRunDetail,
  AnalysisRunStatus,
  SecurityFindingClassification,
  Severity,
} from '../../types';

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

export interface SampleFinding {
  classification: SecurityFindingClassification;
  severity: Severity;
}

// AÇIKÇA ÖRNEK VERİ: liste yanıtında (AnalysisRunList) bulgu alanı yoktur; gerçek bulgu özeti
// güvenlik API'si bağlanınca (#41) buradan kalkar. Gerçek bir tarama sonucu değildir.
export const SAMPLE_FINDINGS_BY_RUN: Readonly<Record<number, SampleFinding>> = {
  1: { classification: 'VERIFIED', severity: 'HIGH' },
};

export interface OverviewMetrics {
  projectCount: number;
  runCount: number;
  inProgressCount: number;
  verifiedFindingCount: number;
}

export interface OverviewData {
  isLoading: boolean;
  isError: boolean;
  metrics: OverviewMetrics | null;
  /** En yeni önce. */
  recentRuns: AnalysisRun[];
  /** Aşama şeridi için ayrıntılı (progress içeren) devam eden analizler. */
  activeRuns: AnalysisRunDetail[];
}

export function useOverviewData(): OverviewData {
  const projects = useQuery({
    queryKey: queryKeys.projects.list({ page: 1, page_size: 100 }),
    queryFn: () => listProjects({ page: 1, page_size: 100 }),
  });
  const runs = useQuery({
    queryKey: queryKeys.analysisRuns.list(),
    queryFn: listAnalysisRuns,
  });

  const runList = runs.data;
  const activeIds = (runList ?? []).filter((r) => isInProgress(r.status)).map((r) => r.id);

  // Liste yanıtında progress yoktur; devam edenlerin ayrıntısı ayrıca alınır.
  const active = useQuery({
    queryKey: [...queryKeys.analysisRuns.list(), 'active', activeIds] as const,
    queryFn: () => Promise.all(activeIds.map((id) => getAnalysisRun(id))),
    enabled: runList !== undefined,
  });

  const isLoading = projects.isLoading || runs.isLoading || active.isLoading;
  const isError = projects.isError || runs.isError || active.isError;

  if (!projects.data || !runList) {
    return { isLoading, isError, metrics: null, recentRuns: [], activeRuns: [] };
  }

  const recentRuns = [...runList].sort((a, b) => b.created_at.localeCompare(a.created_at));
  const metrics: OverviewMetrics = {
    projectCount: projects.data.count,
    runCount: runList.length,
    inProgressCount: activeIds.length,
    verifiedFindingCount: runList.filter(
      (r) => SAMPLE_FINDINGS_BY_RUN[r.id]?.classification === 'VERIFIED',
    ).length,
  };

  return { isLoading, isError, metrics, recentRuns, activeRuns: active.data ?? [] };
}
