// DEMO analiz kayıtları (H5-02 / #40 prototipi). AÇIKÇA ÖRNEK VERİDİR; gerçek backend kaydı değildir ve
// yalnızca /demo/analyses rotalarında kullanılır. Gerçek analizler `analysis-runs.ts` üzerinden gelir;
// gerçek bir analiz kimliği hiçbir zaman bu örnek sonuçlarla eşleştirilmez.
import type { AnalysisRun, AnalysisRunDetail, ApiError, Project } from '../../types';
import { createSampleProjects, mockAnalysisRuns } from './mock';

function toListItem(detail: AnalysisRunDetail): AnalysisRun {
  const { requirements_snapshot: _s, generated_test_count: _g, progress: _p, ...row } = detail;
  return row;
}

export function listDemoAnalysisRuns(): Promise<AnalysisRun[]> {
  return Promise.resolve(mockAnalysisRuns.map(toListItem));
}

export function getDemoAnalysisRun(id: number): Promise<AnalysisRunDetail> {
  const found = mockAnalysisRuns.find((r) => r.id === id);
  return found
    ? Promise.resolve({ ...found })
    : Promise.reject({ status: 404, body: { detail: 'DEMO analiz bulunamadı.' } } satisfies ApiError);
}

/** DEMO analizlerin bağlı olduğu örnek projeler (gerçek proje listesinden ayrıdır). */
export function listDemoProjects(): Promise<Project[]> {
  return Promise.resolve(createSampleProjects());
}
