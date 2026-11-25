import { ThemeToggle } from '../ui/ThemeToggle';
import { UserMenu } from './UserMenu';

export function Topbar() {
  return (
    <header className="flex h-14 shrink-0 items-center justify-end gap-3 border-b border-border bg-surface px-6">
      <ThemeToggle />
      <UserMenu />
    </header>
  );
}
