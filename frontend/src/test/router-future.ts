import type { FutureConfig } from 'react-router-dom';

/** React Router v6 -> v7 uyarılarını susturan ortak bayraklar (main.tsx ve testlerde aynı). */
export const ROUTER_FUTURE: Partial<FutureConfig> = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
};
