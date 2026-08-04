import { create } from 'zustand';
import { storage } from '@/utils/storage';

/**
 * The app's theme — one owner, one class.
 *
 * ── Why this store exists ──
 *
 * Dark mode used to have two independent writers of the same `dark` class:
 *
 *   1. `useDarkMode()` held it in React state, and DashboardLayout stamped it on
 *      its own root <div>.
 *   2. AppearanceTab mutated `documentElement` / `body` imperatively and never
 *      touched that React state.
 *
 * Tailwind's class strategy activates `dark:` when ANY ancestor carries `.dark`,
 * which made switching asymmetric:
 *
 *   Light → Dark   AppearanceTab ADDS `.dark` to <html>. <html> is an ancestor
 *                  of everything, so every variant flips at once. The layout
 *                  div's missing class is irrelevant — instant.
 *
 *   Dark → Light   AppearanceTab REMOVES `.dark` from <html>, but the React
 *                  state is still `true`, so the layout div — which wraps the
 *                  whole app — still carries `.dark`. Every variant inside stays
 *                  on and nothing visibly changes, until a remount re-reads
 *                  localStorage and drops the stale class.
 *
 * Adding a class at the root masks a stale nested one; removing it does not.
 * So: `documentElement` is now the only carrier and `setTheme` the only writer.
 */

/** The three options the Appearance tab offers. */
export const THEMES = ['light', 'dark', 'custom'];

/** Kept in sync with the pre-paint script in index.html. */
const BODY_BG = { dark: '#0c101a', light: '#ffffff' };

const systemQuery = () =>
  typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null;

/** `custom` follows the OS; the other two are explicit. */
export const resolveDark = (theme) =>
  theme === 'dark' || (theme === 'custom' && !!systemQuery()?.matches);

/**
 * The paint — a synchronous class write, deliberately separate from the store
 * update so the flip never waits on React or on persistence.
 *
 * `body` gets the class too because modals portal to it, landing outside the
 * React tree but still inside <html>.
 */
const paint = (isDark) => {
  if (typeof document === 'undefined') return;
  document.documentElement.classList.toggle('dark', isDark);
  if (!document.body) return;
  document.body.classList.toggle('dark', isDark);
  document.body.style.backgroundColor = isDark ? BODY_BG.dark : BODY_BG.light;
};

/**
 * A first-time visitor gets light.
 *
 * Must stay in step with the pre-paint script in index.html, which treats "no
 * stored theme" as light. While this said 'dark' the two disagreed: the script
 * painted light, then this module's reconcile pass immediately flipped it to
 * dark — a first load that flashed light and then landed dark.
 */
const stored = storage.getTheme();
const initialTheme = THEMES.includes(stored) ? stored : 'light';

export const useThemeStore = create((set) => ({
  theme: initialTheme,
  isDark: resolveDark(initialTheme),

  /**
   * Order matters: paint, then state, then persist.
   *
   * The class flip is what the user sees, so nothing may run ahead of it — least
   * of all a localStorage write. Both directions run this one path, so Dark and
   * Light cannot drift apart again.
   */
  setTheme: (theme) => {
    if (!THEMES.includes(theme)) return;
    const isDark = resolveDark(theme);
    paint(isDark);
    set({ theme, isDark });
    storage.setTheme(theme);
  },
}));

/*
 * `custom` is described to the user as "adapts to system preferences", so an OS
 * flip has to reach the app while it is open, not only on the next reload.
 */
systemQuery()?.addEventListener('change', () => {
  if (useThemeStore.getState().theme !== 'custom') return;
  const isDark = resolveDark('custom');
  paint(isDark);
  useThemeStore.setState({ isDark });
});

/*
 * index.html paints from localStorage before React boots to avoid a flash, but
 * it cannot resolve `custom` against the OS. Reconcile once here so the two can
 * never disagree.
 */
paint(resolveDark(initialTheme));
