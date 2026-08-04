import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Remembers which Workspace view the user was last in — AI View (`/workspace/:domain`)
 * or Dashboard View (`/workspace/dashboard/:domain`) — and which domain tab.
 *
 * Navigating away (History, New Analysis, …) and back returns the user to the
 * same place instead of always defaulting to AI View.
 *
 * The persisted field was called `lastIntelTab` before the Workspace rename.
 * `migrate` carries an existing value across, so returning users keep their
 * place; without it the rename would silently reset everyone to 'sales'.
 */
export const useViewModeStore = create(
  persist(
    (set) => ({
      dashboardView: false, // false = AI View, true = Dashboard View
      lastWorkspaceDomain: 'sales',
      setDashboardView: (value) => set({ dashboardView: value }),
      setLastWorkspaceDomain: (domain) => set({ lastWorkspaceDomain: domain }),
    }),
    {
      name: 'realify-view-mode',
      version: 1,
      migrate: (persisted, version) => {
        if (version === 0 && persisted && 'lastIntelTab' in persisted) {
          const { lastIntelTab, ...rest } = persisted;
          return { ...rest, lastWorkspaceDomain: lastIntelTab };
        }
        return persisted;
      },
    }
  )
);
