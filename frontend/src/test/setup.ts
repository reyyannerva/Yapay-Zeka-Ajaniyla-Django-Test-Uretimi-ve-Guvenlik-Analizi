import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';

import { __resetClientStateForTests } from '../lib/api/client';
import { tokenStore } from '../lib/api/token-store';
import { fakeFetch, resetFakeApi } from './fake-api';

// Her test sahte HTTP backend'iyle (fake-api.ts) ve temiz bir oturumla başlar.
beforeEach(() => {
  resetFakeApi();
  tokenStore.clear();
  __resetClientStateForTests();
  try {
    window.sessionStorage.clear();
  } catch {
    /* yok sayılır */
  }
  vi.stubGlobal('fetch', vi.fn(fakeFetch));
  // Varsayılan: oturum açmış kullanıcı (bellekte access token). Anonim akışları test eden dosyalar
  // `tokenStore.clear()` ile başlar.
  tokenStore.setTokens({ access: 'test-access' });
});

afterEach(() => {
  cleanup();
});

// Recharts ResponsiveContainer, jsdom'da bulunmayan ResizeObserver'a ihtiyaç duyar.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
if (!('ResizeObserver' in globalThis)) {
  Object.defineProperty(globalThis, 'ResizeObserver', { value: ResizeObserverStub, writable: true });
}
