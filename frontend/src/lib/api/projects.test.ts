import { vi } from 'vitest';

import { resetMockProjects } from './mock';
import { createProject, deleteProject, listProjects, updateProject } from './projects';

afterEach(resetMockProjects);

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

// --- Sunucu davranışı simülasyonu (docs/api/projects.md) ---

test('createProject aynı adı 400 ile reddeder', async () => {
  await expect(
    createProject({ name: 'Örnek Proje A', archive: new File(['x'], 'a.zip') }),
  ).rejects.toMatchObject({
    status: 400,
    body: { name: ['Bu adla kayıtlı bir projeniz zaten var.'] },
  });
});

test('createProject sunucunun 413 (boyut sınırı) yanıtını olduğu gibi iletir', async () => {
  // Boyut sınırı sunucudadır; jsdom FormData'sı sahte `size` özelliğini kopyalamadığından yanıt taklit edilir.
  vi.mocked(fetch).mockResolvedValueOnce(
    new Response(JSON.stringify({ detail: 'Yüklenen dosya en fazla 52428800 bayt olabilir.' }), {
      status: 413,
      headers: { 'content-type': 'application/json' },
    }),
  );
  await expect(createProject({ name: 'Büyük', archive: new File(['x'], 'b.zip') })).rejects.toMatchObject({
    status: 413,
    body: { detail: 'Yüklenen dosya en fazla 52428800 bayt olabilir.' },
  });
});

test('createProject .zip olmayan arşivi 400 (UNSUPPORTED_TYPE) ile reddeder', async () => {
  await expect(
    createProject({ name: 'Tar', archive: new File(['x'], 'a.tar') }),
  ).rejects.toMatchObject({ status: 400, body: { archive: [{ code: 'UNSUPPORTED_TYPE' }] } });
});

test('deleteProject devam eden analizi olan projeyi 409 ile reddeder', async () => {
  await expect(deleteProject(1)).rejects.toMatchObject({
    status: 409,
    body: { detail: 'Projenin devam eden bir analizi var; analiz bitmeden proje silinemez.' },
  });
});

test('deleteProject analizi olmayan projeyi siler; olmayan projede 404', async () => {
  await expect(deleteProject(3)).resolves.toBeUndefined();
  await expect(deleteProject(3)).rejects.toMatchObject({ status: 404 });
});

test('updateProject başka bir projenin adını 400 ile reddeder', async () => {
  await expect(updateProject(2, { name: 'Örnek Proje A' })).rejects.toMatchObject({ status: 400 });
});
