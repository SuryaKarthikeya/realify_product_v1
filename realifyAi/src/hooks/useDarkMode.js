import { useCallback } from 'react';
import { useThemeStore } from '@/store/useThemeStore';

/**
 * Dark mode as a boolean, for components that swap assets rather than classes —
 * the sidebar logos, chart tooltip colours.
 *
 * Still a `[value, setter]` tuple so existing callers are untouched, but it no
 * longer writes the `dark` class or persists anything: `useThemeStore` owns
 * both, and `documentElement` is the class's only carrier. Two writers of one
 * class is what made Dark → Light fail to apply — see the store for the detail.
 */
export const useDarkMode = () => {
  const isDark = useThemeStore((s) => s.isDark);
  const setTheme = useThemeStore((s) => s.setTheme);

  /* Accepts a boolean or an updater, matching the useState API it replaced. */
  const setDarkMode = useCallback(
    (next) => {
      const value = typeof next === 'function' ? next(useThemeStore.getState().isDark) : next;
      setTheme(value ? 'dark' : 'light');
    },
    [setTheme]
  );

  return [isDark, setDarkMode];
};
