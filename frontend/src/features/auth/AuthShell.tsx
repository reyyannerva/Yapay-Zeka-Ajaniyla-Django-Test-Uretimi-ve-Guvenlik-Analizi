import type { ReactNode } from 'react';
import { ThemeToggle } from '../../components/ui/ThemeToggle';

/** Kalkan logosu — J kimliği markası (TestKalkan). */
function Shield({ className }: { className?: string }) {
  return (
    <svg className={className} width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 2l8 3v6c0 5-3.4 8.5-8 11-4.6-2.5-8-6-8-11V5l8-3z" fill="currentColor" />
      <path
        d="M8.5 12l2.4 2.4L15.7 9.6"
        style={{ stroke: 'var(--panel)' }}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

const STEPS = [
  { n: '1', title: 'Kaynak kod analizi', desc: 'URL, view ve izinler kod çalıştırılmadan çıkarılır.' },
  { n: '2', title: 'Test üretimi', desc: 'Referans kurallarınıza göre Pytest testleri yazılır.' },
  { n: '3', title: 'İzole çalıştırma', desc: "Testler ağ erişimi olmayan bir Docker sandbox'ta koşar." },
  { n: '4', title: 'Bulgu raporu', desc: 'Açıklar doğrulanmış, olası, belirsiz olarak ayrılır.' },
];

interface AuthShellProps {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  children: ReactNode;
}

/** Kimlik doğrulama ekranlarının ortak düzeni: marka paneli (md+) + form alanı (J kimliği). */
export function AuthShell({ title, subtitle, eyebrow, children }: AuthShellProps) {
  return (
    <div className="flex min-h-screen bg-app-bg text-fg">
      <aside className="hidden w-1/2 max-w-xl flex-col justify-center gap-7 bg-gradient-to-b from-panel to-panel-2 p-10 text-panel-fg md:flex">
        <span className="inline-flex items-center gap-2.5 font-display text-xl font-bold text-white">
          <Shield className="text-accent" />
          TestKalkan
        </span>
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.12em] text-white/70">
            Django · DRF · Güvenlik
          </p>
          <h2 className="mt-4 font-display text-3xl font-bold leading-tight text-white">
            Django projenizin testlerini yazar, yetki açıklarını çalışan sistemde doğrular.
          </h2>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-panel-muted">
            Projenizi yükleyin ve uygulamanın nasıl davranması gerektiğini tanımlayın. Gerisini
            TestKalkan yapar.
          </p>
        </div>
        <ol className="flex flex-col border-t border-white/10">
          {STEPS.map((s) => (
            <li
              key={s.n}
              className="grid grid-cols-[auto_1fr] items-start gap-3.5 border-b border-white/10 py-4"
            >
              <span className="grid h-7 w-7 place-items-center rounded-full bg-white/10 font-mono text-sm font-semibold text-white">
                {s.n}
              </span>
              <div>
                <h3 className="text-sm font-semibold text-white">{s.title}</h3>
                <p className="mt-0.5 text-[13px] leading-snug text-panel-muted">{s.desc}</p>
              </div>
            </li>
          ))}
        </ol>
        <div className="font-mono text-xs tracking-wide text-panel-muted">
          Yapay Zekâ ve Veri Mühendisliği Tasarımı · 2026
        </div>
      </aside>
      <main className="relative flex flex-1 items-center justify-center px-4 py-10">
        <div className="absolute right-4 top-4">
          <ThemeToggle />
        </div>
        <div className="w-full max-w-sm">
          <span className="mb-6 inline-flex items-center gap-2 font-display text-lg font-semibold md:hidden">
            <Shield className="text-accent" />
            TestKalkan
          </span>
          {eyebrow ? (
            <p className="font-mono text-xs uppercase tracking-[0.12em] text-accent">{eyebrow}</p>
          ) : null}
          <h1 className="mt-2 font-display text-2xl font-semibold">{title}</h1>
          {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
          <div className="mt-6">{children}</div>
        </div>
      </main>
    </div>
  );
}
