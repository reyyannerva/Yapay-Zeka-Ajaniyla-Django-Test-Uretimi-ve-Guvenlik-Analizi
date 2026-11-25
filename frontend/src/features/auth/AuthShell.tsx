import type { ReactNode } from 'react';

interface AuthShellProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

/** Kimlik doğrulama ekranlarının ortak düzeni: marka paneli (md+) + form alanı. */
export function AuthShell({ title, subtitle, children }: AuthShellProps) {
  return (
    <div className="flex min-h-screen bg-app-bg text-fg">
      <aside className="hidden w-1/2 max-w-xl flex-col justify-between bg-gradient-to-b from-panel to-panel-2 p-10 text-panel-fg md:flex">
        <span className="font-display text-2xl font-semibold">Test ve Güvenlik</span>
        <div>
          <p className="font-display text-3xl font-semibold leading-tight">
            Django projeleriniz için yapay zekâ destekli test üretimi ve güvenlik analizi.
          </p>
          <p className="mt-4 text-sm text-panel-muted">
            Projeyi yükleyin, testleri üretin, sonuçları ve bulguları tek yerden izleyin.
          </p>
        </div>
        <span className="text-xs text-panel-muted">Akademik prototip</span>
      </aside>
      <main className="flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-sm">
          <span className="mb-6 block font-display text-lg font-semibold md:hidden">
            Test ve Güvenlik
          </span>
          <h1 className="font-display text-2xl font-semibold">{title}</h1>
          {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
          <div className="mt-6">{children}</div>
        </div>
      </main>
    </div>
  );
}
