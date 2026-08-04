import { create } from 'zustand';
import { persist } from 'zustand/middleware';

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
      removeStore: (id) =>
        set((state) => ({
          connectedStores: state.connectedStores.filter((s) => s.id !== id),
        })),
    }),
    { name: 'realify-marketplace-stores' }
  )
);
