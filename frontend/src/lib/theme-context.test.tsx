import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import { ThemeToggle } from '../components/ui/ThemeToggle';
import { ThemeProvider } from './theme-context';

beforeEach(() => {
  document.documentElement.removeAttribute('data-theme');
  try {
    window.localStorage.clear();
  } catch {
    /* yoksay */
  }
});

afterEach(() => {
  vi.restoreAllMocks();
});

test('varsayılan açık temadır ve toggle koyuya çevirir', async () => {
  render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>,
  );
  expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  await userEvent.click(screen.getByRole('button'));
  expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
});

test('tercih localStorage erişilemezse açık temaya düşer (throw yutulur)', () => {
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
    throw new Error('localStorage erişilemez');
  });
  expect(() =>
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    ),
  ).not.toThrow();
  expect(document.documentElement.getAttribute('data-theme')).toBe('light');
});
