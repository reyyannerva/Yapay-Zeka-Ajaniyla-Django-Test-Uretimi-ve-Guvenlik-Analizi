import type { AnalysisRun, AnalysisRunDetail } from '../../types';
import { mockAnalysisRuns } from './mock';

// Mock servis. Analiz oluşturma (createAnalysisRun) #40/#41 kapsamıdır, burada yoktur.

/** Liste yanıtı `progress` ve ayrıntı alanlarını içermez (AnalysisRunList). */
function toListItem(detail: AnalysisRunDetail): AnalysisRun {
  const { requirements_snapshot: _s, generated_test_count: _g, progress: _p, ...row } = detail;
  return row;
}

export function listAnalysisRuns(): Promise<AnalysisRun[]> {
  return Promise.resolve(mockAnalysisRuns.map(toListItem));
}

export function getAnalysisRun(id: number): Promise<AnalysisRunDetail> {
  const found = mockAnalysisRuns.find((r) => r.id === id);
  return found
    ? Promise.resolve({ ...found })
    : Promise.reject({
        status: 404,
        body: { detail: 'No AnalysisRun matches the given query.' },
      });
}
