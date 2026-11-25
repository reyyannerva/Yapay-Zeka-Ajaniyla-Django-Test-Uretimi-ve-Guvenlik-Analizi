// JWT saklama (H5-03 / #41).
//
// - Access token yalnızca bellekte tutulur (sayfa yenilenince kaybolur, depolamaya yazılmaz).
// - Refresh token sessionStorage'da tutulur: sekmeye özeldir, sekme kapanınca silinir, localStorage gibi
//   tüm sekmelerle ve kalıcı olarak paylaşılmaz. Sayfa yenilemede oturumun sürmesini sağlar.
//   Backend refresh token'ı JSON gövdede verir (HttpOnly çerez sözleşmesi yoktur); XSS riski bilinçli
//   olarak kabul edilip azaltılır: kısa access süresi, refresh rotasyonu + kara liste, çıkışta kara liste,
//   uygulamada HTML enjeksiyonu yok (dangerouslySetInnerHTML kullanılmaz). Ayrıntı: docs/integration/h5-03.
// - Token'lar URL'ye, konsola veya hata mesajlarına yazılmaz.
// - `generation` her temizlemede artar; çıkıştan önce başlamış bir yenileme yanıtı oturumu geri getiremez.

import type { AuthTokens } from '../../types';

const REFRESH_KEY = 'testkalkan.refresh';

let access: string | null = null;
let generation = 0;

function storage(): Storage | null {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

export const tokenStore = {
  getAccess(): string | null {
    return access;
  },
  getRefresh(): string | null {
    try {
      return storage()?.getItem(REFRESH_KEY) ?? null;
    } catch {
      return null;
    }
  },
  /** Giriş veya yenileme sonrası; rotasyonda yeni refresh token da yazılır. */
  setTokens(tokens: Partial<AuthTokens> & { access: string }): void {
    access = tokens.access;
    if (tokens.refresh) {
      try {
        storage()?.setItem(REFRESH_KEY, tokens.refresh);
      } catch {
        /* depolama yoksa oturum yalnızca bu sayfa ömrü boyunca sürer */
      }
    }
  },
  clear(): void {
    access = null;
    generation += 1;
    try {
      storage()?.removeItem(REFRESH_KEY);
    } catch {
      /* yok sayılır */
    }
  },
  generation(): number {
    return generation;
  },
  hasSession(): boolean {
    return access !== null || this.getRefresh() !== null;
  },
};
