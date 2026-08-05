import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Connected marketplaces, persisted per browser.
 *
 * Add-only on purpose: the UI offers no disconnect anywhere, so there is no
 * single-store removal action to call. Clearing everything is the account-level
 * "Wipe data & re-onboard" flow, which clears localStorage outright.
 */
export const useMarketplaceStore = create(
  persist(
    (set) => ({
      connectedStores: [],
      addStore: (store) =>
        set((state) => ({
          connectedStores: [
            ...state.connectedStores.filter((s) => s.id !== store.id),
            store,
          ],
        })),
    }),
    { name: 'realify-marketplace-stores' }
  )
);
