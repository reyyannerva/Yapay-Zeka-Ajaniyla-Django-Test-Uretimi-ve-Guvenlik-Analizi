import { useCallback, useEffect, useState } from 'react';
import { Outlet } from 'react-router-dom';

import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export function AppLayout() {
  const [navOpen, setNavOpen] = useState(false);
  const closeNav = useCallback(() => setNavOpen(false), []);

  useEffect(() => {
    if (!navOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setNavOpen(false);
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [navOpen]);

  return (
    <div className="flex min-h-screen bg-app-bg text-fg">
      {navOpen && (
        <div
          data-testid="sidebar-scrim"
          aria-hidden="true"
          onClick={closeNav}
          className="fixed inset-0 z-30 bg-scrim md:hidden"
        />
      )}
      <Sidebar open={navOpen} onClose={closeNav} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar navOpen={navOpen} onMenuClick={() => setNavOpen((v) => !v)} />
        <main className="flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
