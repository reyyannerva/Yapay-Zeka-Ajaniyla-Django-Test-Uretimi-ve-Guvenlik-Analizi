import { NavLink } from 'react-router-dom';

interface NavItem {
  label: string;
  to: string;
  /** Pasif öğeler henüz uygulanmamış sayfalardır (#40); link olarak çizilmez. */
  disabled?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Genel bakış', to: '/dashboard' },
  { label: 'Projeler', to: '/projects' },
  { label: 'Analizler', to: '/analysis', disabled: true },
  { label: 'Raporlar', to: '/reports', disabled: true },
];

const ITEM_BASE = 'block border-l-2 px-4 py-2 text-sm';

export function Sidebar() {
  return (
    <aside className="flex w-56 shrink-0 flex-col bg-gradient-to-b from-panel to-panel-2 text-panel-fg">
      <div className="px-4 py-5 font-display text-lg font-semibold">Test ve Güvenlik</div>
      <nav aria-label="Ana menü" className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) =>
          item.disabled ? (
            <span
              key={item.to}
              aria-disabled="true"
              title="Yakında"
              className={`${ITEM_BASE} cursor-not-allowed border-transparent text-panel-muted opacity-60`}
            >
              {item.label}
            </span>
          ) : (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `${ITEM_BASE} focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent ${
                  isActive
                    ? 'border-accent bg-white/10 font-medium text-panel-fg'
                    : 'border-transparent text-panel-muted hover:text-panel-fg'
                }`
              }
            >
              {item.label}
            </NavLink>
          ),
        )}
      </nav>
    </aside>
  );
}
