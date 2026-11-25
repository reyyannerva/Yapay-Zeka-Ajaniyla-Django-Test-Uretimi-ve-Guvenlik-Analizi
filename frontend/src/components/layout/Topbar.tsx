import { ThemeToggle } from '../ui/ThemeToggle';
import { SIDEBAR_ID } from './Sidebar';
import { UserMenu } from './UserMenu';

interface TopbarProps {
  navOpen: boolean;
  onMenuClick: () => void;
}

export function Topbar({ navOpen, onMenuClick }: TopbarProps) {
  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border bg-surface px-4 md:px-6">
      <button
        type="button"
        onClick={onMenuClick}
        aria-label="Menüyü aç"
        aria-expanded={navOpen}
        aria-controls={SIDEBAR_ID}
        className="inline-flex items-center rounded-md border border-border bg-surface p-2 text-fg hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent md:hidden"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          <path d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <div className="ml-auto flex items-center gap-3">
        <ThemeToggle />
        <UserMenu />
      </div>
    </header>
  );
}
