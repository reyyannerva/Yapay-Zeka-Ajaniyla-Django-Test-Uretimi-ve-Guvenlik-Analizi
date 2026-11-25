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

export const SIDEBAR_ID = 'app-sidebar';

interface SidebarProps {
  /** md altında kenar menüsü çekmece (drawer) olarak açık mı. */
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  // md ve üstünde her zaman kalıcı panel; altında yalnızca `open` iken sabit çekmece.
  const visibility = open ? 'fixed inset-y-0 left-0 z-40 flex md:static md:z-auto' : 'hidden md:flex';

  return (
    <aside
      id={SIDEBAR_ID}
      className={`${visibility} w-56 shrink-0 flex-col bg-gradient-to-b from-panel to-panel-2 text-panel-fg`}
    >
      <div className="flex items-center justify-between px-4 py-5">
        <span className="font-display text-lg font-semibold">Test ve Güvenlik</span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Menüyü kapat"
          className="rounded p-1 text-panel-muted hover:text-panel-fg focus-visible:outline focus-visible:outline-2 focus-visible:outline-panel-accent md:hidden"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>
      </div>
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
              onClick={onClose}
              className={({ isActive }) =>
                `${ITEM_BASE} focus-visible:outline focus-visible:outline-2 focus-visible:outline-panel-accent ${
                  isActive
                    ? 'border-panel-accent bg-panel-active font-medium text-panel-fg'
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
