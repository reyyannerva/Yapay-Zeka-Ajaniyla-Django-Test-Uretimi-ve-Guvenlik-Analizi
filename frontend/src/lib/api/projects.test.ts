import { createProject, listProjects } from './projects';

test('listProjects sayfalı tip döndürür ve en yeni önce gelir', async () => {
  const page = await listProjects();
  expect(page).toHaveProperty('count');
  expect(Array.isArray(page.results)).toBe(true);
  expect(page.results[0]).toHaveProperty('validation_status');
  const dates = page.results.map((p) => p.created_at);
  expect([...dates].sort().reverse()).toEqual(dates);
});

test('createProject verilen adla Project döndürür', async () => {
  const p = await createProject({ name: 'Örnek', description: '', archive: new File([], 'x.zip') });
  expect(p.name).toBe('Örnek');
  expect(p.id).toBeTruthy();
});
