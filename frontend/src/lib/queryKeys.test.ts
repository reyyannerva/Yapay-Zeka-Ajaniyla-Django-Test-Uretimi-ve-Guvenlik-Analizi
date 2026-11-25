import { queryKeys } from './queryKeys';

test('queryKeys kararlı ve ayırt edicidir', () => {
  expect(queryKeys.projects.detail(1)).toEqual(queryKeys.projects.detail(1));
  expect(queryKeys.projects.detail(1)).not.toEqual(queryKeys.projects.detail(2));
});
