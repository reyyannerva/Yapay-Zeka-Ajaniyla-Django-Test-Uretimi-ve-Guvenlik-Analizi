export const queryKeys = {
  auth: {
    me: () => ['auth', 'me'] as const,
  },
  projects: {
    all: () => ['projects'] as const,
    list: (params?: { page?: number; page_size?: number }) =>
      ['projects', 'list', params ?? {}] as const,
    detail: (id: number) => ['projects', 'detail', id] as const,
  },
  /** Gerçek backend analiz kayıtları (H5-03 / #41). */
  analysisRuns: {
    all: () => ['analysis-runs'] as const,
    list: () => ['analysis-runs', 'list'] as const,
    detail: (id: number) => ['analysis-runs', 'detail', id] as const,
  },
  /** Gerçek backend referans gereksinim kayıtları (H5-03 / #41). */
  referenceRequirements: {
    all: () => ['reference-requirements'] as const,
    list: () => ['reference-requirements', 'list'] as const,
  },
  /**
   * DEMO (H5-02 prototipi) verileri ayrı bir ad alanındadır; gerçek kayıtların önbelleğiyle karışmaz.
   */
  demo: {
    projects: () => ['demo', 'projects'] as const,
    analysisRuns: {
      list: () => ['demo', 'analysis-runs', 'list'] as const,
      detail: (id: number) => ['demo', 'analysis-runs', 'detail', id] as const,
      endpoints: (id: number) => ['demo', 'analysis-runs', 'detail', id, 'endpoints'] as const,
      tests: (id: number) => ['demo', 'analysis-runs', 'detail', id, 'tests'] as const,
      results: (id: number) => ['demo', 'analysis-runs', 'detail', id, 'results'] as const,
      findings: (id: number) => ['demo', 'analysis-runs', 'detail', id, 'findings'] as const,
      evaluation: (id: number) => ['demo', 'analysis-runs', 'detail', id, 'evaluation'] as const,
    },
  },
};
