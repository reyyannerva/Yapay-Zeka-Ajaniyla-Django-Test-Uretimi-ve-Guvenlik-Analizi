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
  analysisRuns: {
    all: () => ['analysis-runs'] as const,
    list: () => ['analysis-runs', 'list'] as const,
    detail: (id: number) => ['analysis-runs', 'detail', id] as const,
  },
};
