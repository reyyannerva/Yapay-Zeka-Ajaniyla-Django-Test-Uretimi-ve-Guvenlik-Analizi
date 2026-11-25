import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';

interface NavItem {
  label: string;
  to: string;
  icon: ReactNode;
  /** Pasif öğeler henüz uygulanmamış sayfalardır (#40); link olarak çizilmez. */
  disabled?: boolean;
}

function Icon({ path }: { path: string }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="shrink-0"
    >
      <path d={path} />
    </svg>
  );
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Genel bakış', to: '/dashboard', icon: <Icon path="M3 11l9-8 9 8M5 10v10h14V10" /> },
  { label: 'Projeler', to: '/projects', icon: <Icon path="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2z" /> },
  { label: 'Analizler', to: '/analyses', icon: <Icon path="M3 12h4l3 7 4-14 3 7h4" /> },
  { label: 'Deney sonuçları', to: '/experiments', icon: <Icon path="M4 20V10M10 20V4M16 20v-7M22 20H2" /> },
  { label: 'Raporlar', to: '/reports', icon: <Icon path="M7 3h7l5 5v13H7zM14 3v5h5" />, disabled: true },
];

const ITEM_BASE = 'flex items-center gap-3 border-l-2 px-4 py-2 text-sm';

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
        <span className="inline-flex items-center gap-2.5 font-display text-lg font-bold text-white">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true" className="text-accent">
            <path d="M12 2l8 3v6c0 5-3.4 8.5-8 11-4.6-2.5-8-6-8-11V5l8-3z" fill="currentColor" />
            <path d="M8.5 12l2.4 2.4L15.7 9.6" style={{ stroke: 'var(--panel)' }} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          TestKalkan
        </span>
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
              {item.icon}
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
              {item.icon}
              {item.label}
            </NavLink>
          ),
        )}
      </nav>
    </aside>
  );
}
