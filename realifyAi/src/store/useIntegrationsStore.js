import { create } from 'zustand';
import { storage } from '@/utils/storage';

/**
 * Which connectors the user has taken all the way through onboarding.
 *
 * The wizard step already says "where am I right now", but it lives in the URL
 * and is gone the moment the user leaves the page — so it cannot answer "is this
 * connector set up?". That question is asked by three separate surfaces (the
 * catalogue's primary button, the detail header, the onboarding journey rail),
 * and they must never disagree, so the answer is stored once here and persisted.
 */
export const useIntegrationsStore = create((set) => ({
  completedIds: storage.getCompletedSetups(),

  /** Idempotent — reaching Go live twice is a no-op, so it is safe from an effect. */
  completeSetup: (id) => set((state) => {
    if (!id || state.completedIds.includes(id)) return state;
    const completedIds = [...state.completedIds, id];
    storage.setCompletedSetups(completedIds);
    return { completedIds };
  }),

  resetCompletedSetups: () => {
    storage.setCompletedSetups([]);
    return set({ completedIds: [] });
  },
}));

/**
 * Has this connector finished setup?
 *
 * Selects a boolean rather than the array so a component only re-renders when
 * its own connector's answer changes, not on every other connector's completion.
 */
export const useSetupComplete = (connectorId) =>
  useIntegrationsStore((s) => (connectorId ? s.completedIds.includes(connectorId) : false));
